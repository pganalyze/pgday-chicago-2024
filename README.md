# Constraint Programming Model for Index Selection in Postgres (PGDay Chicago 2024)

This repository contains everything necessary to run the constraint programming model for index selection presented in the PGDay Chicago 2024 talk [Automating Index Selection Using Constraint Programming](https://postgresql.us/events/pgdaychicago2024/schedule/session/1561-automating-postgres-index-selection-using-constraint-programming/).

Creating indexes on a table in order to meet some requirements (performance, resource budget, etc) is typically done by hand. This model can be used as part of automation that suggests a selection of good indexes to meet arbitrary user requirements. These requirements are expressed in terms of [goals](#goals) and [rules](#rules).

We (pganalyze) are sharing this model in an effort to further the discussion about automating Postgres index selection within the broader Postgres community. A more sophisticated variant of this model is available with the [pganalyze Indexing Engine](https://pganalyze.com/docs/indexing-engine), which you can utilize as part of the Index Advisor available in [pganalyze](https://pganalyze.com/).

⭐️ **Note:** To run this model end-to-end in a development environment, we recommend taking a look at [pganalyze_lint](https://github.com/pganalyze/lint/tree/main), which takes care of passing the right inputs to the model based on your local query workload.


## Getting Started

[Python 3.6+](https://www.python.org/downloads) and the OR-Tools package are needed. The official installation instructions can be found [here](https://developers.google.com/optimization/install/python), but in short:

```bash
$ python3 -m pip install --upgrade --user ortools
```


## Running the Index Selection Model

You can immediately run the model on the example data. From the main directory:

```bash
$ python3 src/main.py -d examples/data_example.json
```

This will find the indexes that minimize the combined costs of the scans, using as few indexes as needed. The output of this command is explained [here](#model-output). To use custom settings:

```bash
$ python3 src/main.py -d examples/data_example.json -s examples/settings_example.json
```

For details on the various options:

```bash
$ python3 src/main.py -h
```


## Data

The model needs data in JSON format as input. Example data files are provided in the `examples` directory. The script `src/datagen.py` allows the creation of custom data files. First, modify the values of the constants in the source code of the script to the desired values. Then, the command

```bash
$ python3 datagen.py data.json
```

will create a data file named `data.json` with the desired values.


## Settings (Goals and Rules)

The model may also be provided with a settings file in JSON format, containing goals and rules. This file should contain one goal at a minimum. An example settings file is provided in the `examples` directory.


### Goals

Goals are the main components that guide the model towards a solution. A combination of up to three goals can be chosen.

**Minimize Total Cost**: Minimize the combined cost of all the scans.

**Minimize Number of Indexes**: Minimize the number of indexes that are selected.

**Minimize Index Write Overhead**: Minimize the combined index write overhead (IWO) of the existing and possible indexes that are selected.


### Rules

Two rules can be enforced by the model.

**Maximum Number of Possible Indexes**: Do not select more than X possible indexes.

**Maximum Index Write Overhead**: The combined IWO of the selected indexes (existing and possible) may not be higher than X.


### Default Settings

If no settings are selected by the user, the model will fall back to the default, which is to minimize the combined costs of the scans, using the fewest indexes:

```json
{
    "Options": {
        "Goals": [
            {
                "Name": "Minimize Total Cost",
                "Tolerance": 0.0
            },
            {
                "Name": "Minimize Number of Indexes"
            }
        ]
    }
}
```


### Ordering the Goals and Tolerance

When optimizing for multiple goals, these goals must be ordered by preference. The ordering of goals by preference does not need to be absolute, but can instead be made more flexible by specifying a tolerance parameter for the goals.

The tolerance parameter is a measure of how strict the ordering of the goals is. Each goal has an associated tolerance value in the range [0.0, ∞] (defaulted to 0). When a goal is optimized, the resulting value indicates how well that goal has met its stated objective. The tolerance of that goal, in turn, indicates how close subsequent goals should stick to the value found for the original goal.


#### Example of the Process

Suppose that the settings are as follows:

```json
{
    "Goals": [
        {
            "Name": "Minimize Total Cost",
            "Tolerance": 0.1
        },
        {
            "Name": "Minimize Index Write Overhead"
        }
    ],
    "Rules":
    {
        "Maximum Number of Possible Indexes": 4
    }
}
```

In other words: *The combined costs of the scans should be within a 10% margin of the best possible costs. Use as little IWO to achieve this. Up to 4 possible indexes may be used for that purpose.*

The solving process will be as follows:

```txt
1. Find the lowest combined costs of the scans that can be achieved by using no more than 4 indexes.
2. Find a combination of up to 4 possible indexes that can offer combined scan costs no worse than 110% of what was found in (1), that use a little IWO as possible.
```


## Model Output

A sample output of the model with some comments:

```json
{
    "Goals": [                               // List of goals in order
        {
            "Minimize Total Cost": 212.2     // First goal and its associated value
        },
        {
            "Minimize Number of Indexes": 1  // Second goal and its associated value
        }
    ],
    "Scans": [                               // List of all scans
        {
            "Scan ID": "Scan A",             // Scan name
            "Cost": 42.2,                    // Best cost for this scan in the solution
            "Best Covered By": 3             // Which index offers this cost to the scan
        },
        {
            "Scan ID": "Scan B",
            "Cost": 150.7,
            "Best Covered By": null          // This scan is not covered by any index
        },
        {
            "Scan ID": "Scan C",
            "Cost": 19.3,
            "Best Covered By": 4
        }
    ],
    "Indexes": {
        "Existing Indexes": [                // List of all existing indexes
            {
                "Index OID": 4,              // Index name
                "Selected": true             // Is this index selected in the solution?
            },
        ],
        "Possible Indexes": [                // List of all possible indexes
            {
                "Index OID": 1,
                "Selected": false
            },
            {
                "Index OID": 2,
                "Selected": false
            },
            {
                "Index OID": 3,
                "Selected": true
            }
        ]
    },
    "Statistics": {                          // List of statistics
        "Coverage": {                        // Coverage information
            "Total": 2,                      // Number of scans convered by indexes
            "Existing": 1,                   // Number of scans best convered by existing indexes
            "Possible": 1,                   // Number of scans best convered by possible indexes
            "Uncovered": 1                   // Number of scans not covered by any index
        },
        "Cost": {                            // Cost information
            "Total": 212.2,                  // Total costs of all the scans
            "Maximum": 150.7                 // Highest cost found among the scans
        },
        "Indexes Used": {                    // Index information
            "Total": 2,                      // Number of indexes present in the solution
            "Existing": 1,                   // Number of existing indexes present in the solution
            "Possible": 1                    // Number of possible indexes present in the solution
        },
        "Index Write Overhead": {            // IWO information
            "Total": 0.81,                   // Combined IWO of all the indexes present in the solution
            "Existing": 0.49,                // Combined IWO of all the existing indexes present in the solution
            "Possible": 0.32                 // Combined IWO of all the possible indexes present in the solution
        }
    }
}
```


## License

This repository is licensed under the 3-clause BSD license, see LICENSE file for details.

Copyright (c) 2024, Duboce Labs, Inc. (pganalyze)
