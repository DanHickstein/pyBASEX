# Contributing to PyAbel




### Adding a new forward or inverse Abel implementation 

We are always looking for new implementation of forward or inverse Abel transform, therefore if you have an implementation that you would want to contribute to PyAbel, don't hesitate to do so. 


In order to allow a consistent user experience between different implementations, and insure an overall code quality, please consider the following points in your pull request.

##### Naming conventions

The implementation named `<implementation>`, located under `abel/<implementation>.py` should use the following naming system for top-level functions,

 -  `fabel_<implemenation>`  :  forward transform (when defined)
 -  `iabel_<implemenation>` :  inverse implementation (when defined)
 -  `_bs_<implementation>` :  function that generates  the basis sets (if necessary)
 -  `bs_<implementation>_cached` : function that loads the basis sets from disk, and generates them if they are not found (if necessary).


##### Unit tests

As to detect issues early and avoid regressions, the submitted implementation should have the following properties and pass the corresponding unit tests,

 1. The reconstruction has the same shape as the original image for the parity (even/odd shape of the image) it supports. When provided with an image size with a parity it does not support a clear exception should be raised.

 2. Given an array of 0 elements, the reconstruction should also be a 0 array.
  
 3. The implementation should be able to calculated the inverse (or forward) transform of a Gaussian function defined by a standard deviation `sigma`, with better than a `10 %` relative error with respect to the analytical solution for `0 > r > 2*sigma`.


Unit tests for a given implementation are located under `abel/tests/test_<implemenation>.py`, which should contain at least the following 3 functions `test_<implementation>_shape`, `test_<implementation>_zeros`, `test_<implementation>_gaussian`. See `abel/tests/test_basex.py` for a concrete example.


The test suite can be run from within the PyAbel package with,
  
    nose -s  abel/tests/ --verbosity=2  --with-coverage --cover-package=abel

or, from any folder with,
    
    python  -c "import abel.tests; abel.tests.run_cli(coverage=True)"

which performs an equivalent call.

Note that this requires that you have [Nose](nose.readthedocs.org) and (optionally) [Coverage](coverage.readthedocs.org) installed. You can install these with:

	pip install nose
	pip install coverage
	
  
##### Dependencies

The current list of dependencies can be found in [`setup.py`](https://github.com/PyAbel/PyAbel/blob/master/setup.py). Please refrain from adding new dependencies, unless it cannot be avoided.


##### Documentation

PyAbel uses Sphinx and [Napoleon](http://sphinxcontrib-napoleon.readthedocs.org/en/latest/index.html) to process Numpy style docstrings, and is synchronized to [pyabel.readthedocs.org](http://pyabel.readthedocs.org/). To build the documentation locally, you will need Sphinx, the [`recommonmark`](https://github.com/rtfd/recommonmark) package, and the [`sphinx_rtd_theme`](https://github.com/snide/sphinx_rtd_theme/). Then, you can build the documentation using

	 cd PyAbel/doc/
	 make html
 
See the discussion on [PR #69](https://github.com/PyAbel/PyAbel/pull/69) for more information. 


##### Before merging

If possible, before merging your pull request please rebase your fork on the last master on PyAbel. This could be done  [as explained in this post](https://stackoverflow.com/questions/7244321/how-to-update-a-github-forked-repository),
   
    # Add the remote, call it "upstream" (only the fist time)
    git remote add upstream git@github.com:PyAbel/PyAbel.git

    # Fetch all the branches of that remote into remote-tracking branches,
    # such as upstream/master:

    git fetch upstream

    # Make sure that you're on your master branch 
    # or any other branch your are working on

    git checkout master  # or your other working branch

    # Rewrite your master branch so that any commits of yours that
    # aren't already in upstream/master are replayed on top of that
    # other branch:

    git rebase upstream/master

    # push the changes to your fork
 
    git push -f

See [this wiki](https://github.com/edx/edx-platform/wiki/How-to-Rebase-a-Pull-Request) for more information.
