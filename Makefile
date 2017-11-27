all: git-commit

.PHONY: git-commit
git-commit:
	git checkout
	git add setup.py Makefile  >> .local.git.out  || echo
	git commit -a -m 'Commit' >> .local.git.out || echo 
	git push origin master	


