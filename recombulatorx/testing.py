import itertools
import numpy
from . import ProcessedFamily
##########################
# TEST FAMILY GENERATION #
##########################


def generate_random_rates(n_markers: int):
    """Generate random recombination and mutation rates.

    Rates are intended to be not too unrealistic for the human X chromosome.
    Thus, rates are always lower than 0.5 for recombination and 0.05 for mutation
    and the total of the recombination rates is capped at 2.

    n_markers: int
    Number of markers
    
    Returns:
    a tuple of recombination (n_markers - 1) and mutation (n_markers) rates.
    """
    m = numpy.square(numpy.random.rand(n_markers))*0.05
    r = numpy.square(numpy.random.rand(n_markers - 1)*0.5)
    # avoid eccessive recombination which is unrealistic
    s = sum(r)
    if s > 2:
        r = r/s
    return r, m

def generate_haplotypes(n_markers: int, n_haps: int, mode='STR'):
    """
    Generate random haplotypes
    """
    if mode == 'STR':
        base = 10*numpy.arange(1, n_markers + 1)
        noise = numpy.random.randn(n_haps, n_markers)
        haps = base + numpy.clip(numpy.round(3*noise) + 5, 1, 9)
    elif mode == 'SNP':
        alleles = list('ACGT')
        acc = []
        for i in range(n_markers):
            # generate allele freqs for each marker
            p = (numpy.random.random(len(alleles))*[1, 0.5, 0.1, 0.01])**2
            p = p/numpy.sum(p)
            numpy.random.shuffle(p)
            acc.append(numpy.random.choice(alleles, size=n_haps, p=p))
        haps = numpy.array(acc).T
    return haps

def mutate_haplotypes(haps, mutation_rates, mode='STR'):
    """Add random mutations to haplotypes"""
    n_haps, n_markers = haps.shape
    mut_mask = (numpy.random.rand(n_haps, n_markers) < mutation_rates)
    if mode == 'STR':
        muts = (2*numpy.random.randint(2, size=(n_markers, n_haps)) - 1)*mut_mask.T
        mut_haps = haps + muts.T
    elif mode == 'SNP':
        alleles = 'ACGT'
        b2i = {c: i for i, c in enumerate(alleles)}
        i2b = dict(enumerate(alleles))
        ihaps = numpy.vectorize(b2i.get)(haps)
        muts = numpy.random.randint(1, len(alleles), size=haps.shape)
        mut_haps = numpy.vectorize(i2b.get)((ihaps + muts*mut_mask) % len(alleles))
    return mut_haps

def generate_maternal_haplotypes(mother, n_haps: int, recombination_rates, mutation_rates, mode='STR'):
    n_markers = mother.shape[0]
    recomb = (numpy.random.rand(n_haps, n_markers - 1) < recombination_rates).T

    #null_values = dict(STR=numpy.nan, 'N')
    #if mode == 'STR':
    #haps = numpy.full((n_haps, n_markers), -1.0 if)
    haps = numpy.full((n_haps, n_markers), numpy.nan, dtype=(object if mode == 'SNP' else float))
    #print(n_haps, n_markers, haps.shape, haps)
    #elif mode == 'SNP':
    #    haps = numpy.fu

    current_hap = numpy.random.randint(2, size=n_haps)
    for i in range(n_markers):
        haps[:, i] = mother[i, current_hap]
        if i < n_markers - 1:
            current_hap[recomb[i]] = 1 - current_hap[recomb[i]]

    return mutate_haplotypes(haps, mutation_rates, mode=mode)

def generate_processed_family(fid: str, n_sons: int, is_mother_phased: bool, recombination_rates, mutation_rates, mode='STR'):
    mother = generate_haplotypes(len(mutation_rates), 2, mode=mode).T
    haps = generate_maternal_haplotypes(mother, n_sons, recombination_rates, mutation_rates, mode=mode)
    return ProcessedFamily(
        fid=fid,
        is_mother_phased=is_mother_phased,
        mother=mother,
        maternal_haplotypes=haps
    )

def generate_complex_family(fid: str, is_mother_phasable: bool, n_sons: int, n_daughters: int, recombination_rates, mutation_rates, mode='STR'):
    """Generate a realistic family, with sons, daughters (with father) and an optional grandfather"""
    pf = generate_processed_family(fid, n_sons + n_daughters, is_mother_phased=is_mother_phasable, recombination_rates=recombination_rates, mutation_rates=mutation_rates, mode=mode)
    mother, mat_haps = pf.mother, pf.maternal_haplotypes
    if is_mother_phasable:
        # then add the mother's father
        yield (
            fid, 'GRANDFATHER', None, None, 
            mutate_haplotypes(mother.T[:1], mutation_rates),
        )
    yield (
        fid, 'MOTHER', 'GRANDFATHER' if is_mother_phasable else None, None, 
        numpy.sort(mother.T, axis=0),
    )
    
    # add sons
    for i, mat_hap in enumerate(mat_haps[:n_sons]):
        yield (
            fid, f'SON_{i + 1}', None, 'MOTHER', 
            numpy.array([mat_hap]),
        )

    # generate one father for each daughter
    father_haps = generate_haplotypes(len(mutation_rates), n_daughters)
    for i, (father_hap, pat_hap, mat_hap) in enumerate(zip(
        father_haps, mutate_haplotypes(father_haps, mutation_rates), mat_haps[n_sons:])):
        yield (
            fid, f'FATHER_{i+1}', None, None, 
            numpy.array([father_hap]),
        )
        yield (
            fid, f'DAUGHTER_{i+1}', f'FATHER_{i+1}', 'MOTHER', 
            numpy.sort([pat_hap, mat_hap], axis=0),
        )

def generate_complex_families(n_fam_I: int, n_fam_II: int, recombination_rates, mutation_rates):
    for i in range(n_fam_I + n_fam_II):
        typeI = i < n_fam_I
        n_children = max(1 if typeI else 2, numpy.random.poisson(2.0))
        n_sons = numpy.random.binomial(n_children, 0.5)
        fid = f'FAM_{i}_' + ('I' if typeI else 'II')
        for ind in generate_complex_family(
            fid=fid, n_sons=n_sons, 
            n_daughters=n_children - n_sons, 
            is_mother_phasable=typeI, 
            recombination_rates=recombination_rates, 
            mutation_rates=mutation_rates):
            yield ind

def individuals2ped(path, marker_names, individuals):
    sex_coding={1: '1', 2: '2'}
    with open(path, 'wt') as ped:
        print('FID', 'IID', 'PAT', 'MAT', 'SEX', 'PHENO', *(f"{m}-A{a + 1}" for m in marker_names for a in range(2)), sep='\t', file=ped)
        for fid, iid, pat, mat, geno in individuals:
            n_haps = geno.shape[0]
            geno0 = numpy.array([geno[0], [0]*geno.shape[1]]) if n_haps == 1 else geno
            sex = sex_coding[n_haps]
            print(fid, iid, pat or 0, mat or 0, sex, -1, *geno0.T.reshape(-1), sep='\t', file=ped)


def compute_family_likelihood_empirical(mother, maternal_haplotypes, is_mother_phased, recombination_rates, mutation_rates):
    """
    Empirical type I family likelihood computation.

    Randomly generates possible maternal haplotypes with the given rates and
    counts how many times the given maternal haplotypes are generated.

    """
    assert is_mother_phased
    n_markers = mother.shape[0]
    haps = generate_maternal_haplotypes(mother, 100*(2**n_markers), recombination_rates, mutation_rates)
    lh_acc = [
        numpy.sum(
            numpy.all(hap == haps, axis=1))/haps.shape[0]
        for hap in maternal_haplotypes
    ]
    return numpy.prod(lh_acc)


def generate_processed_families(n_type_I: int, n_type_II: int, n_sons: int, recombination_rates, mutation_rates):
    pfams = []
    for i in range(n_type_I):
        mother, sons = generate_processed_family(n_sons, recombination_rates, mutation_rates)
        pfams.append(dict(
            fid=f"type_I_{i + 1}",
            mother=mother,
            is_mother_phased=True,
            maternal_haps=sons,
        ))
    for i in range(n_type_II):
        mother, sons = generate_processed_family(n_sons, recombination_rates, mutation_rates)
        pfams.append(dict(
            fid=f"type_II_{i + 1}",
            mother=mother,
            is_mother_phased=False,
            maternal_haps=sons,
        ))
    return pfams

# testing part
def run_test():
    from xstr_recomb.likelihood_dyn import compute_phased_family_likelihood_dyn_loop, compute_phased_family_likelihood_dyn_loop_numba, compute_phased_family_likelihood_dyn_vec, compute_unphased_family_likelihood_dyn_queue

    from xstr_recomb.likelihood import precompute_probs, compute_family_likelihood
    numpy_probs = None # this needs to be defined before calling the function
    def compute_phased_family_likelihood_numpy(mother, maternal_haplotypes, recombination_rates, mutation_rates):
        return compute_family_likelihood(mother, maternal_haplotypes, True, numpy_probs['r'], numpy_probs['inheritance_matrix'], numpy_probs['inheritance_probs'], numpy_probs['mutation_probs'])
    def compute_unphased_family_likelihood_numpy(mother, maternal_haplotypes, recombination_rates, mutation_rates):
        return compute_family_likelihood(mother, maternal_haplotypes, False, numpy_probs['r'], numpy_probs['inheritance_matrix'], numpy_probs['inheritance_probs'], numpy_probs['mutation_probs'])

    type_I_funcs = {
        'numpy': compute_phased_family_likelihood_numpy,
        'dyn_loop': compute_phased_family_likelihood_dyn_loop, 
        'dyn_vec': compute_phased_family_likelihood_dyn_vec, 
        'dyn_numba': compute_phased_family_likelihood_dyn_loop_numba, 
    }
    type_II_funcs = {
        'numpy': compute_unphased_family_likelihood_numpy,
        'dyn_queue': compute_unphased_family_likelihood_dyn_queue,
        'dyn_queue~es0.1': lambda *x: compute_unphased_family_likelihood_dyn_queue(*x, early_stop=0.1), 
    }

    import time
    from xstr_recomb.testing import generate_processed_families, generate_random_rates

    import matplotlib.pyplot as plt
    import seaborn
    import pandas
    max_time = 0.05
    n_fam_I = 10
    n_fam_II = 10
    time_df_acc = {}
    slow_funcs = set()
    for n_markers in range(2, 100):
        print(n_markers)
        rates = generate_random_rates(n_markers)
        numpy_probs = None
        #rand_recomb_rates, rand_mut_rates = 
        processed_fams_I = generate_processed_families(n_fam_I, 0, 3, *rates)
        processed_fams_II = generate_processed_families(0, n_fam_II, 3, *rates)
        time_acc = {}
        for processed_fams, funcs in [(processed_fams_I, type_I_funcs), (processed_fams_II, type_II_funcs)]: 
            for fname, f in funcs.items():
                for i, pf in enumerate(processed_fams):
                    ftype = 'type I' if pf['is_mother_phased'] else 'type II'
                    if (fname, ftype) in slow_funcs: continue
                    if fname == 'numpy':
                        numpy_probs = precompute_probs(*rates)
                    t0 = time.time()
                    lh = f(pf['mother'], pf['maternal_haps'], *rates)
                    t1 = time.time()
                    time_acc[(fname, ftype, i)] = [lh, t1 - t0]
        if len(time_acc) == 0:
            break
        
        df = pandas.DataFrame(time_acc, index=['lh', 'dt']).T
        df.index.names = ['func', 'fam', 'rep']

        # check if any function is taking too long
        mean_dt = df.reset_index().groupby(['func', 'fam'])['dt'].mean()
        new_slow = set(mean_dt.index[mean_dt > max_time])
        slow_funcs |= new_slow
        print(n_markers, new_slow)

        time_df_acc[n_markers] = df.reset_index()
        full_df = pandas.concat(time_df_acc, names=['n_markers', 'row']).reset_index('row', drop=True).reset_index()
