# TODO: SCRUB
import logging
import os
from pathlib import Path

import psutil
import pytest

from graph_sitter.codebase.config import ProjectConfig
from graph_sitter.codebase.validation import PostInitValidationStatus, post_init_validation
from graph_sitter.configs.models.codebase import CodebaseConfig
from graph_sitter.core.codebase import Codebase
from graph_sitter.git.repo_operator.repo_operator import RepoOperator
from tests.shared.codemod.models import Repo
from tests.shared.utils.recursion import set_recursion_limit

BYTES_IN_GIGABYTE = 1024**3
MAX_ALLOWED_GIGABYTES = 31
logger = logging.getLogger(__name__)

# Path to skip file for problematic repositories
SKIP_TESTS_DIR = Path(__file__).parent / "repos" / "open_source" / ".skiptests"
LARGE_REPOS_SKIP_FILE = SKIP_TESTS_DIR / "large_repos.txt"


@pytest.mark.timeout(60 * 12, func_only=True)
def test_codemods_parse(repo: Repo, op: RepoOperator, request) -> None:
    # Check if this repository should be skipped
    if LARGE_REPOS_SKIP_FILE.exists() and repo.name in LARGE_REPOS_SKIP_FILE.read_text().splitlines():
        pytest.skip(f"Skipping {repo.name} as it's known to cause segmentation faults")
    
    # Setup Feature Flags
    sync = request.config.getoption("sync-graph").lower() == "true"
    log_parse = request.config.getoption("log-parse").lower() == "true"
    if repo.config is not None:
        codebase_config = repo.config
    else:
        codebase_config = CodebaseConfig()

    codebase_config = codebase_config.model_copy(update={"verify_graph": sync, "debug": log_parse, "ignore_process_errors": False})

    set_recursion_limit()
    
    # Monitor memory usage before creating the codebase
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    logger.info(f"Initial memory usage: {initial_memory / BYTES_IN_GIGABYTE:.2f} GB")
    
    # Setup Codebase with memory monitoring
    try:
        projects = [ProjectConfig(repo_operator=op, programming_language=repo.language, subdirectories=repo.subdirectories)]
        codebase = Codebase(projects=projects, config=codebase_config)
        
        # Check memory usage after codebase creation
        memory_used = process.memory_info().rss
        memory_increase = memory_used - initial_memory
        logger.info(f"Using {memory_used / BYTES_IN_GIGABYTE:.2f} GB of memory (increase: {memory_increase / BYTES_IN_GIGABYTE:.2f} GB)")
        
        # Fail if memory usage is too high
        assert memory_used <= BYTES_IN_GIGABYTE * MAX_ALLOWED_GIGABYTES, f"Graph is using too much memory! ({memory_used / BYTES_IN_GIGABYTE:.2f} GB)"
        
        # Validate the codebase
        validation_res = post_init_validation(codebase)
        if validation_res != PostInitValidationStatus.SUCCESS:
            msg = f"Graph failed post init validation: {validation_res}!"
            raise Exception(msg)
    except MemoryError:
        logger.error(f"Memory error while processing {repo.name}. Consider adding it to the skip list.")
        pytest.skip(f"Memory error while processing {repo.name}")
