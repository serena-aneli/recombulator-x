---
sort: 3
permalink: /usage
---

# Usage

## File formats

recombulator-x uses a file organized as a PED files ([PLINK](https://www.cog-genomics.org/plink/ pedigree file) as input. The pedigree file can be a *.tsv* (tab as separator value), a *.xlsx* or whatever format with a space as separator value. The PED file format stores sample pedigree information (i.e., the familial relationships between samples) and the genotypes.
In particular, the first 6 mandatory columns contain: 

* Family ID
* Individual ID
* Paternal ID
* Maternal ID
* Sex
* Phenotype

The "Sex" field may be coded as: 1=male/2=female; XY=male/XX=female; M=male/F=female; MALE=male/FEMALE=female. If you are using STR markers, you can store within this column the Amelogenin marker. 

The "Phenotype" field refers to the use of PED files in medical research. In non-medical application, it may be -9 which means "unknown".
        
From the 7th column on, there are the markers genotypes (two columns for a genetic marker, each of the two storing an allele). In case of STRs, the columns contain  numbers, which correspond to the STR repeats or "0" when missing. 

:warning: **Important**: Genetic markers (from the 7th column on) must be provided according to their physical genomic position. Indeed, the algorithm will infer the recombination rate between A1 and A2, A2 and A3 and so on.

### Example

Here is a family (each row is an individual):

| **FID** |   **IID**   |   **PAT**   | **MAT** | **SEX** | **PHENO** | **STR1-A1** | **STR1-A2** | **STR2-A1** | **STR2-A2** | **STR3-A1** | **STR3-A2** |
|:-------:|:-----------:|:-----------:|:-------:|:-------:|:---------:|:----------:|:----------:|:----------:|:----------:|:----------:|:----------:|
| FAM_I | GRANDFATHER | 0           | 0       | 1       | -9        | 12         | 0          | 29         | 0          | 39         | 0          |
| FAM_I | MOTHER      | GRANDFATHER | 0       | 2       | -9        | 12         | 16         | 27         | 29         | 34         | 39         |
| FAM_I | SON_1       | 0           | MOTHER  | 1       | -9        | 12         | 0          | 29         | 0          | 34         | 0          |
| FAM_I | FATHER_1    | 0           | 0       | 1       | -9        | 14         | 0          | 21         | 0          | 37         | 0          |
| FAM_I | DAUGHTER_1  | FATHER_1    | MOTHER  | 2       | -9        | 14         | 16         | 21         | 27         | 34         | 37         |
| FAM_I | FATHER_2    | 0           | 0       | 1       | -9        | 18         | 0          | 25         | 0          | 36         | 0          |
| FAM_I | DAUGHTER_2  | FATHER_2    | MOTHER  | 2       | -9        | 12         | 18         | 25         | 29         | 36         | 39         |

---

## Python module and workflow

A detailed guide for the Python module usage can be found in the Jupyter Notebook [Estimation Example.ipynb](https://github.com/serena-aneli/recombulator-x/blob/gh-pages/Estimation%20Example.ipynb) on GitHub. 

The initial steps of the Python module recombulator-x consist in reading the PED file and identifying the informative families for the estimation of recombination rates using the function `ped2graph`. This function takes a ped file as input and build a graph with the relationships. It returns a list of tuples, each composed by the graph, a dictionary (with iid as key and their tab row as value) and the family identifier. 

The pedigree file can be a *.tsv* (tab as separator value), a *.xlsx* or whatever format with a space as separator value.

For recombination, informative subfamilies are either those with:

- a phased mother and at least one son or phased daughter, called type I families
- an unphased mother and at least two between sons and phased daughters, called type II families

Notably, females can be phased when their father is available: in this way, they will be virtually transformed into males, thus being allowed to take part to informative families.
 
The function `plot_family_graph` can then be used to graphically represent the reported relationships between individuals within the same family. 

```python
family_graphs, marker_names = recombulatorx.ped2graph(ped_path)
xstr_recomb.families.plot_family_graph(family_graphs[0][1]) 
```

The fuction `preprocess_families` will then check the consistency of each family graph and raise errors whenever necessary. For instance, an error is raised when more than two parents or same-sex parents are present in the same family. Unconnected individuals are also flagged.

```python
processed_families = recombulatorx.preprocess_families(family_graphs)
```

The estimation of recombination and mutation rates can be launched with the following line:

```python
est_recomb_rates, est_mut_rates = recombulatorx.estimate_rates(processed_families, 0.1, 0.1, estimate_mutation_rates='all')
```

The function *estimate_rates* estimates recombination and mutation rates from a set of families and takes the following parameters: 

* the families, 
* the initial recombination rate, 
* the initial mutation rate, 
* which mutation rate needs to be estimated (*no*: no mutation rate estimation, *one*: just one mutation rate for all markers, *all*: a mutation rate for each marker),
* the type of implementation (the default implementation is the one using dynamic programming).

An example of output generated by function \emph{estimate_rates} in Python is: 

```    
(array([0.03874299, 0.32869992, 0.01459788, 0.19265765, 0.01016452]),
 array([1.00000000e-08, 1.00000000e-08, 1.23511804e-01, 2.10614659e-02, 2.24679981e-03, 1.00000000e-08]))
```
       
where, the first array (n-1 long) stores the recombination rates, while the second (n long) contains the mutation rates estimated for simulated families and six X-STRs.

## Command line tool

The command line interface of recombulator-x takes as input the PED file and returns recombination and mutation rates.  

```text
usage: recombulator-x [-h] [--mutation-rates MUT-RATE [MUT-RATE ...]]
                      [--estimate-mutation-rates {no,one,all}]
                      PED

Estimate recombination and mutation rates.

positional arguments:
  PED                   path to ped file

optional arguments:
  -h, --help            show this help message and exit
  --mutation-rates MUT-RATE [MUT-RATE ...]
                        mutation rates used in the estimation, either
                        as fixed or as starting point in the
                        optimization depending on the value of the
                        --estimate-mutation-rates option. If not
                        given the rates are set to 0.001 for all
                        markers
  --estimate-mutation-rates {no,one,all}
                        controls the estimation of the mutation
                        rates. With "no" the mutation rates are not
                        estimated, with "one" the same rate is
                        estimated for all markers, with "all" a
                        separate estimation rate is estimated for
                        each marker. Defaults to "no"
```

Its basic usage consists in estimating just recombination rate and using the default single value for mutation rate (0.001).

```Bash
recombulator-x ped_path
``` 

Alternatively, one may also decide to estimate mutation rates. In particular, adding `--estimate-mutation-rates all`, the tool will compute a mutation value for each marker. 

```Bash
recombulator-x ped_path --estimate-mutation-rates all
```

## Output 

The output of recombulator-x command line interface is returned in a tabular format according to the options *no*, *one*, *all* for the parameter `--estimate-mutation-rates` (Tables 1-3). In particular, the recombination rates are computed between markers following the order in which they were provided in the PED file.


| TYPE          | MARKER | RATE   |       
|---------------|--------|--------|
| RECOMBINATION | M1-M2  | 0.0362 |
| RECOMBINATION | M2-M3  | 0.3309 |
| RECOMBINATION | M3-M4  | 0.0656 |
| RECOMBINATION | M4-M5  | 0.1683 |
| RECOMBINATION | M5-M6  | 0.0138 |

Table 1: recombulator-x output when `--estimate-mutation-rates no` is used.


| TYPE          | MARKER | RATE   |       
|---------------|--------|--------|
| MUTATION      | *      | 0.0253 |
| RECOMBINATION | M1-M2  | 0.0323 |
| RECOMBINATION | M2-M3  | 0.3191 |
| RECOMBINATION | M3-M4  | 0.0407 |
| RECOMBINATION | M4-M5  | 0.1634 |
| RECOMBINATION | M5-M6  | 0.0091 |
 
Table 2: recombulator-x output when `--estimate-mutation-rates one` is used.
        

| TYPE          | MARKER | RATE   |        
|---------------|--------|--------|
| MUTATION      | M1     | 1e-08  |
| MUTATION      | M2     | 1e-08  |
| MUTATION      | M3     | 0.1420 |
| MUTATION      | M4     | 0.0191 |
| MUTATION      | M5     | 1e-08  |
| MUTATION      | M6     | 1e-08  |
| RECOMBINATION | M1-M2  | 0.0366 |
| RECOMBINATION | M2-M3  | 0.3148 |
| RECOMBINATION | M3-M4  | 0.0214 |
| RECOMBINATION | M4-M5  | 0.1605 |
| RECOMBINATION | M5-M6  | 0.0141 |
        
Table 3: recombulator-x output when `--estimate-mutation-rates all` is used.





 



