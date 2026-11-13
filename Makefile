# make all            tools check + every test + synthesis
# make test           every test        make test BLOCK=alu   one block
# make synth          synthesis         make tools            record versions
.PHONY: all test synth tools clean
all: tools test synth
tools:
	@scripts/versions.sh
test:
	@scripts/run_tests.sh $(BLOCK)
synth:
	@scripts/synth.sh $(BLOCK)
clean:
	rm -rf build
