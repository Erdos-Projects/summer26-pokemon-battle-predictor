#!/usr/bin/env zsh
grep -r "import [[:alnum:]_]\+" --include="*.py" --include="*.ipynb" --exclude-dir=.ipynb_checkpoints ./../.. > search_results.txt
grep -r "from [[:alnum:]_]\+ import" --include="*.py" --include="*.ipynb" --exclude-dir=.ipynb_checkpoints ./../.. >> search_results.txt