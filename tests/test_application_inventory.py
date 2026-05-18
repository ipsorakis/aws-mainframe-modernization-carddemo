"""Tests for application inventory completeness and consistency.

Validates that the full application inventory (programs, maps, copybooks,
JCL, data files) is complete and internally consistent.
"""
import pathlib

import pytest


class TestOnlineTransactionInventory:
    """Verify the online transaction inventory from the README is complete."""

    # TransID -> (BMS Map, Program) from the application inventory
    ONLINE_TRANSACTIONS = {
        "CC00": ("COSGN00", "COSGN00C"),
        "CM00": ("COMEN01", "COMEN01C"),
        "CAVW": ("COACTVW", "COACTVWC"),
        "CAUP": ("COACTUP", "COACTUPC"),
        "CCLI": ("COCRDLI", "COCRDLIC"),
        "CCDL": ("COCRDSL", "COCRDSLC"),
        "CCUP": ("COCRDUP", "COCRDUPC"),
        "CT00": ("COTRN00", "COTRN00C"),
        "CT01": ("COTRN01", "COTRN01C"),
        "CT02": ("COTRN02", "COTRN02C"),
        "CR00": ("CORPT00", "CORPT00C"),
        "CB00": ("COBIL00", "COBIL00C"),
        "CA00": ("COADM01", "COADM01C"),
        "CU00": ("COUSR00", "COUSR00C"),
        "CU01": ("COUSR01", "COUSR01C"),
        "CU02": ("COUSR02", "COUSR02C"),
        "CU03": ("COUSR03", "COUSR03C"),
    }

    @pytest.mark.parametrize(
        "trans_id,mapping",
        list(ONLINE_TRANSACTIONS.items()),
        ids=list(ONLINE_TRANSACTIONS.keys()),
    )
    def test_bms_map_exists(self, bms_dir, trans_id, mapping):
        bms_name, _ = mapping
        assert (bms_dir / f"{bms_name}.bms").exists(), (
            f"Transaction {trans_id}: BMS map {bms_name}.bms missing"
        )

    @pytest.mark.parametrize(
        "trans_id,mapping",
        list(ONLINE_TRANSACTIONS.items()),
        ids=list(ONLINE_TRANSACTIONS.keys()),
    )
    def test_cobol_program_exists(self, cbl_dir, trans_id, mapping):
        _, program = mapping
        assert (cbl_dir / f"{program}.cbl").exists(), (
            f"Transaction {trans_id}: program {program}.cbl missing"
        )

    @pytest.mark.parametrize(
        "trans_id,mapping",
        list(ONLINE_TRANSACTIONS.items()),
        ids=list(ONLINE_TRANSACTIONS.keys()),
    )
    def test_program_references_trans_id(self, cbl_dir, trans_id, mapping):
        """Each program should reference its own transaction ID."""
        _, program = mapping
        filepath = cbl_dir / f"{program}.cbl"
        text = filepath.read_text()
        assert trans_id in text, (
            f"{program}: doesn't reference transaction ID '{trans_id}'"
        )


class TestBatchJobInventory:
    """Verify batch job inventory is complete."""

    BATCH_JOBS = {
        "POSTTRAN": "CBTRN02C",
        "INTCALC": "CBTRN03C",
    }

    @pytest.mark.parametrize(
        "job,program",
        list(BATCH_JOBS.items()),
        ids=list(BATCH_JOBS.keys()),
    )
    def test_batch_jcl_exists(self, jcl_dir, job, program):
        assert (jcl_dir / f"{job}.jcl").exists(), (
            f"Batch job {job}: JCL missing"
        )

    @pytest.mark.parametrize(
        "job,program",
        list(BATCH_JOBS.items()),
        ids=list(BATCH_JOBS.keys()),
    )
    def test_batch_program_exists(self, cbl_dir, job, program):
        assert (cbl_dir / f"{program}.cbl").exists(), (
            f"Batch job {job}: program {program}.cbl missing"
        )


class TestDataFileInventory:
    """Verify data files match the README installation guide."""

    REQUIRED_DATA_FILES = {
        "acctdata.txt": "CVACT01Y",
        "carddata.txt": "CVACT02Y",
        "cardxref.txt": "CVACT03Y",
        "custdata.txt": "CVCUS01Y",
        "dailytran.txt": "CVTRA06Y",
        "discgrp.txt": "CVTRA02Y",
        "tcatbal.txt": "CVTRA01Y",
        "trancatg.txt": "CVTRA04Y",
        "trantype.txt": "CVTRA03Y",
    }

    @pytest.mark.parametrize(
        "data_file,copybook",
        list(REQUIRED_DATA_FILES.items()),
        ids=list(REQUIRED_DATA_FILES.keys()),
    )
    def test_data_file_has_matching_copybook(
        self, data_ascii_dir, cpy_dir, data_file, copybook
    ):
        assert (data_ascii_dir / data_file).exists(), (
            f"Data file {data_file} missing"
        )
        assert (cpy_dir / f"{copybook}.cpy").exists(), (
            f"Copybook {copybook}.cpy missing for data file {data_file}"
        )


class TestCSDResourceDefinitions:
    """Verify CSD resource definitions exist."""

    def test_csd_directory_exists(self, app_dir):
        csd = app_dir / "csd"
        assert csd.exists(), "CSD directory missing"

    def test_csd_has_definitions(self, app_dir):
        csd = app_dir / "csd"
        if csd.exists():
            files = list(csd.iterdir())
            assert len(files) >= 1, "CSD directory is empty"


class TestSchedulerDefinitions:
    """Verify scheduler configuration exists."""

    def test_scheduler_directory_exists(self, app_dir):
        scheduler = app_dir / "scheduler"
        assert scheduler.exists(), "Scheduler directory missing"

    def test_scheduler_has_definitions(self, app_dir):
        scheduler = app_dir / "scheduler"
        if scheduler.exists():
            files = list(scheduler.iterdir())
            assert len(files) >= 1, "Scheduler directory is empty"


class TestDirectoryStructure:
    """Verify the complete application directory structure."""

    REQUIRED_DIRS = [
        "cbl",
        "cpy",
        "cpy-bms",
        "jcl",
        "bms",
        "data",
        "csd",
        "ctl",
        "scheduler",
    ]

    @pytest.mark.parametrize("dirname", REQUIRED_DIRS)
    def test_app_subdirectory_exists(self, app_dir, dirname):
        assert (app_dir / dirname).exists(), (
            f"Application directory app/{dirname} missing"
        )

    def test_data_has_ascii_and_ebcdic(self, app_dir):
        data = app_dir / "data"
        assert (data / "ASCII").exists(), "data/ASCII directory missing"
        assert (data / "EBCDIC").exists(), "data/EBCDIC directory missing"
