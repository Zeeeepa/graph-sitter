from graph_sitter.codebase.flagging.code_flag import CodeFlag
from graph_sitter.codebase.flagging.group import Group
from graph_sitter.codebase.flagging.groupers.base_grouper import BaseGrouper
from graph_sitter.codebase.flagging.groupers.enums import GroupBy
from graph_sitter.git.repo_operator.repo_operator import RepoOperator
import logging

DEFAULT_CHUNK_SIZE = 5

logger = logging.getLogger(__name__)

class CodeownerGrouper(BaseGrouper):
    """Group flags by CODEOWNERS.

    Parses .github/CODEOWNERS and groups by each possible codeowners

    Segment should be either a github username or github team name.
    """

    type: GroupBy = GroupBy.CODEOWNER

    @staticmethod
    def create_all_groups(flags: list[CodeFlag], repo_operator: RepoOperator | None = None) -> list[Group]:
        owner_to_group: dict[str, Group] = {}
        no_owner_group = Group(group_by=GroupBy.CODEOWNER, segment="@no-owner", flags=[])
        for idx, flag in enumerate(flags):
            flag_owners = repo_operator.codeowners_parser.of(flag.filepath)  # TODO: handle codeowners_parser could be null
            if not flag_owners:
                no_owner_group.flags.append(flag)
                continue
            # NOTE: always use the first owner. ex if the line is /dir @team1 @team2 then use team1
            flag_owner = flag_owners[0][1]
            group = owner_to_group.get(flag_owner, Group(id=idx, group_by=GroupBy.CODEOWNER, segment=flag_owner, flags=[]))
            group.flags.append(flag)
            owner_to_group[flag_owner] = group

        no_owner_group.id = len(owner_to_group)
        return [*list(owner_to_group.values()), no_owner_group]

    @staticmethod
    def create_single_group(flags: list[CodeFlag], segment: str, repo_operator: RepoOperator | None = None) -> Group:
        """Create a single group for the given flags with proper codeowner handling."""
        if not flags:
            return Group(group_by=GroupBy.CODEOWNER, segment=segment, flags=[])
        
        # Use the first flag to determine the group characteristics
        primary_flag = flags[0]
        
        # If repo_operator is available, try to get actual owners
        if repo_operator and hasattr(repo_operator, 'codeowners_parser') and repo_operator.codeowners_parser:
            try:
                flag_owners = repo_operator.codeowners_parser.of(primary_flag.filepath)
                if flag_owners:
                    # Use the first owner as the segment
                    segment = flag_owners[0][1]
            except Exception as e:
                logger.error(f"Error getting codeowners for single group: {e}")
                # Fallback to provided segment or default
                segment = segment or f"unowned_{primary_flag.filepath.stem}"
        
        return Group(
            id=hash(segment),
            group_by=GroupBy.CODEOWNER,
            segment=segment,
            flags=flags
        )

    def _get_flag_owners(self, flag) -> list:
        """Safely get flag owners with null checking and error handling."""
        if not hasattr(self.repo_operator, 'codeowners_parser') or self.repo_operator.codeowners_parser is None:
            logger.warning(f"Codeowners parser not available for {flag.filepath}")
            return []
        
        try:
            return self.repo_operator.codeowners_parser.of(flag.filepath)
        except Exception as e:
            logger.error(f"Error parsing codeowners for {flag.filepath}: {e}")
            return []

    def create_groups(self, flags: list[CodeFlag]) -> list[Group]:
        owner_to_group: dict[str, Group] = {}
        no_owner_group = Group(group_by=GroupBy.CODEOWNER, segment="@no-owner", flags=[])
        for flag in flags:
            flag_owners = self._get_flag_owners(flag)  # Use safe method instead of direct access
            
            if not flag_owners:
                no_owner_group.flags.append(flag)
                continue
            # NOTE: always use the first owner. ex if the line is /dir @team1 @team2 then use team1
            flag_owner = flag_owners[0][1]
            group = owner_to_group.get(flag_owner, Group(id=flag.id, group_by=GroupBy.CODEOWNER, segment=flag_owner, flags=[]))
            group.flags.append(flag)
            owner_to_group[flag_owner] = group

        no_owner_group.id = len(owner_to_group)
        return [*list(owner_to_group.values()), no_owner_group]
