CXX = g++ -fPIC
NETLIBS= -lnsl

all: git-commit timer

timer : timer.o
	$(CXX) -o $@ $@.o $(NETLIBS)

%.o: %.cc
	@echo 'Building $@ from $<'
	$(CXX) -o $@ -c -I. $<

.PHONY: git-commit
git-commit:
	git add timer.cc Makefile >> .local.git.out  || echo
	git commit -a -m 'Commit' >> .local.git.out || echo 

.PHONY: clean
clean:
	rm -f *.o timer

