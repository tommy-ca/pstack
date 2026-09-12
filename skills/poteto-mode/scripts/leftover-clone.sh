# Leftover-clone predicate shared by worktree-audit.sh and worktree-drop.sh.
# Child of leftover-parent, not in porcelain, and not under $repo/.worktrees
# are caller checks. Unmarked clones count. A pin file must equal --repo.
is_leftover_clone() {
	local d="$1" repo="$2" overlay="$3" src
	[ -d "$d/.git" ] || return 1
	[ ! -f "$d/.git" ] || return 1
	case "$d" in
		"$overlay"|"$overlay"/*) return 1 ;;
	esac
	if [ -f "$d/.git/grok-worktree-source" ]; then
		src=$(tr -d '\n' < "$d/.git/grok-worktree-source")
		[ "$src" = "$repo" ] || return 1
	fi
	return 0
}
