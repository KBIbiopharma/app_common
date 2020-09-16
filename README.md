# app_common

| Linux, OSX  | [![Build Status](https://travis-ci.org/KBIbiopharma/app_common.svg?branch=master)](https://travis-ci.org/KBIbiopharma/app_common) |
| ----------- | ----------- |
| Win         | [![Build status](https://ci.appveyor.com/api/projects/status/7fficyruc7myu0mp/branch/master?svg=true)](https://ci.appveyor.com/project/jonathanrocher/app-common/branch/master)       |


## Description

General Python tools and utilities to support building desktop scientific 
applications quickly using the `Enthought Tool Suite` (ETS).

Some of the code in this repository is designed to either remain in this 
repository or to be contributed to the Enthought Tool Suite. External 
contributions, fixes and requests are welcomed and encouraged.

## Content
This package contains a lot of general tools to build new GUI application with 
the following (pre-built) features:

- Customizable pane system,
- Tabbed central pane,
- Logging,
- (Super) simple license management,
- Software update tool,
- Help menus (about dialog, bug reporting instructions, link to
  documentation),
- Script runner (in-process),
- Interactive `IPython` console launcher (out-of-process),
- Preference management (with UI dialog),
- Asynchronous job manager (with a UI pane).

For a new application template, see the `examples/` folder. Alternatively, 
individual pieces and utilities can be used in your own ETS application.


## Dependencies

The project supports and is tested on both Python 2.7 and Python 3.6+. It 
relies on the following open-source projects:

Required dependencies:
* Traits
* TraitsUI
* Pyface
* apptools
* chaco, enable
* numpy
* six

Optional dependencies:
* nose
* scimath (for unitted traits)
* encore, concurrent.futures (for job manager tools)
* h5py, pytables (for project serialization tools)
* scipy
* Matplotlib (for mpl_tools)


## Code organization
Since the tools in this repository are sometimes designed to be pushed
upstream, code is often stored in sub-folders named after the project they
would be the target of the contribution: traits, .... More general, pure-python
tools are to be found in the `std_lib` sub-folder.

See the `CONTRIBUTING.txt` document for how to contribute to this repository.
