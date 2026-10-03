.PHONY: validate figures checksums

validate:
	python -m py_compile run_g4_audit.py run_g4_redesign_audit.py run_g7_experiments.py run_g7_sensitivity.py run_g8_paired_bootstrap.py run_g10_multiseed_threshold_transport.py run_g10_arm_error_audit.py
	python validate_frozen_results.py

figures:
	python make_figures.py

checksums:
	sha256sum $$(git ls-files | grep -v '^SHA256SUMS.txt$$' | sort) > SHA256SUMS.txt
