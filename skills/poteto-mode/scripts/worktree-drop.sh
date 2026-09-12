#!/usr/bin/env bash
# Usage:
#   worktree-drop.sh --repo <primary> --dry-run|--apply \
#     --expect-registered N --expect-leftover N [--leftover-parent DIR] [--path DIR ...]
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
# shellcheck source=leftover-clone.sh
. "$here/leftover-clone.sh"

repo=""
mode=""
expect_registered=""
expect_leftover=""
leftover_parent=""
paths=()

while [ $# -gt 0 ]; do
	case "$1" in
		--repo) repo="${2:?}"; shift 2 ;;
		--dry-run)
			[ -z "$mode" ] || { echo "refusing: --dry-run and --apply are exclusive" >&2; exit 1; }
			mode=dry-run
			shift
			;;
		--apply)
			[ -z "$mode" ] || { echo "refusing: --dry-run and --apply are exclusive" >&2; exit 1; }
			mode=apply
			shift
			;;
		--expect-registered) expect_registered="${2:?}"; shift 2 ;;
		--expect-leftover) expect_leftover="${2:?}"; shift 2 ;;
		--leftover-parent) leftover_parent="${2:?}"; shift 2 ;;
		--path) paths+=("${2:?}"); shift 2 ;;
		*) echo "unknown arg: $1" >&2; exit 2 ;;
	esac
done

[ -n "$repo" ] && [ -n "$mode" ] && [ -n "$expect_registered" ] && [ -n "$expect_leftover" ] || {
	echo "usage: $0 --repo DIR --dry-run|--apply --expect-registered N --expect-leftover N [--leftover-parent DIR] [--path DIR ...]" >&2
	exit 2
}

case "$expect_registered" in
	''|*[!0-9]*)
		echo "refusing: --expect-registered is not a non-negative integer: $expect_registered" >&2
		exit 1
		;;
esac
case "$expect_leftover" in
	''|*[!0-9]*)
		echo "refusing: --expect-leftover is not a non-negative integer: $expect_leftover" >&2
		exit 1
		;;
esac

[ -d "$repo" ] || { echo "refusing: --repo is not a directory: $repo" >&2; exit 1; }
repo=$(cd "$repo" && pwd -P)

case "$repo" in
	*/.worktrees|*/.worktrees/*)
		echo "refusing: --repo $repo is under .worktrees" >&2
		exit 1
		;;
esac

if [ -f "$repo/.git/grok-worktree-source" ]; then
	echo "refusing: --repo $repo is a leftover isolation clone" >&2
	exit 1
fi

common=$(cd "$repo" && cd "$(git rev-parse --git-common-dir)" && pwd -P)
[ "$common" = "$repo/.git" ] || {
	echo "refusing: git-common-dir $common is not $repo/.git" >&2
	exit 1
}

primary=$(git -C "$repo" worktree list --porcelain | sed -n 's/^worktree //p' | sed -n '1p')
[ -n "$primary" ] || { echo "refusing: no git worktree found" >&2; exit 1; }
primary=$(cd "$primary" && pwd -P)
[ "$primary" = "$repo" ] || {
	echo "refusing: porcelain primary $primary is not --repo $repo" >&2
	exit 1
}

overlay="$repo/.worktrees"
if [ -n "$leftover_parent" ]; then
	[ -d "$leftover_parent" ] || {
		echo "refusing: --leftover-parent is not a directory: $leftover_parent" >&2
		exit 1
	}
	leftover_parent=$(cd "$leftover_parent" && pwd -P)
	case "$leftover_parent" in
		"$repo"|"$overlay"|"$overlay"/*)
			echo "refusing: --leftover-parent $leftover_parent is $repo or under $overlay" >&2
			exit 1
			;;
	esac
	case "$repo" in
		"$leftover_parent"|"$leftover_parent"/*)
			echo "refusing: --repo $repo is inside leftover-parent $leftover_parent" >&2
			exit 1
			;;
	esac
else
	[ "$expect_leftover" = 0 ] || {
		echo "refusing: empty leftover-parent requires --expect-leftover 0" >&2
		exit 1
	}
fi

list_registered() {
	git -C "$repo" worktree list --porcelain | sed -n 's/^worktree //p' | tail -n +2
}

path_in_use() {
	local target="$1" cwd resolved
	[ -d /proc ] || return 1
	resolved=$(cd "$target" && pwd -P) 2>/dev/null || return 1
	for cwd in /proc/[0-9]*/cwd; do
		[ -L "$cwd" ] || continue
		got=$(readlink -f "$cwd" 2>/dev/null || true)
		[ -n "$got" ] || continue
		[ "$got" = "$resolved" ] && return 0
		case "$got" in
			"$resolved"/*) return 0 ;;
		esac
	done
	return 1
}

remove_registered=()
while IFS= read -r wt; do
	[ -n "$wt" ] || continue
	wt=$(cd "$wt" && pwd -P)
	if [ "$wt" = "$primary" ]; then
		echo "refusing: would remove primary $wt" >&2
		exit 1
	fi
	remove_registered+=("$wt")
done < <(list_registered)

in_porcelain() {
	local d="$1" live
	while IFS= read -r live; do
		[ -n "$live" ] || continue
		live=$(cd "$live" && pwd -P)
		[ "$d" = "$live" ] && return 0
	done < <(git -C "$repo" worktree list --porcelain | sed -n 's/^worktree //p')
	return 1
}

remove_leftover=()
classify_leftovers() {
	remove_leftover=()
	[ -n "$leftover_parent" ] || return 0
	local d
	while IFS= read -r d; do
		[ -n "$d" ] || continue
		d=$(cd "$d" && pwd -P)
		in_porcelain "$d" && continue
		is_leftover_clone "$d" "$repo" "$overlay" || continue
		remove_leftover+=("$d")
	done < <(find "$leftover_parent" -maxdepth 1 -mindepth 1 -type d | sort)
}

classify_leftovers

if [ "${#remove_registered[@]}" -ne "$expect_registered" ]; then
	echo "refusing: registered_count ${#remove_registered[@]} != --expect-registered $expect_registered" >&2
	exit 1
fi
if [ "${#remove_leftover[@]}" -ne "$expect_leftover" ]; then
	echo "refusing: leftover_count ${#remove_leftover[@]} != --expect-leftover $expect_leftover" >&2
	exit 1
fi

if [ "$mode" = apply ] && [ "${#paths[@]}" -eq 0 ]; then
	if [ "${#remove_registered[@]}" -ne 0 ] || [ "${#remove_leftover[@]}" -ne 0 ]; then
		echo "refusing: --apply requires at least one --path" >&2
		exit 1
	fi
fi

path_in_classified() {
	local p="$1" candidate
	for candidate in "${remove_registered[@]+"${remove_registered[@]}"}"; do
		[ "$p" = "$candidate" ] && return 0
	done
	for candidate in "${remove_leftover[@]+"${remove_leftover[@]}"}"; do
		[ "$p" = "$candidate" ] && return 0
	done
	return 1
}

target_registered=()
target_leftover=()
if [ "${#paths[@]}" -eq 0 ]; then
	if [ "${#remove_registered[@]}" -gt 0 ]; then
		target_registered=("${remove_registered[@]}")
	fi
	if [ "${#remove_leftover[@]}" -gt 0 ]; then
		target_leftover=("${remove_leftover[@]}")
	fi
else
	seen=""
	for p in "${paths[@]}"; do
		[ -d "$p" ] || {
			echo "refusing: --path is not a directory: $p" >&2
			exit 1
		}
		p=$(cd "$p" && pwd -P)
		case "$seen" in
			*"|$p|"*) continue ;;
		esac
		path_in_classified "$p" || {
			echo "refusing: unknown --path $p" >&2
			exit 1
		}
		seen="${seen}|$p|"
		matched=0
		for candidate in "${remove_registered[@]+"${remove_registered[@]}"}"; do
			if [ "$p" = "$candidate" ]; then
				target_registered+=("$p")
				matched=1
				break
			fi
		done
		if [ "$matched" -eq 0 ]; then
			target_leftover+=("$p")
		fi
	done
fi

printf "primary\t%s\n" "$primary"
printf "mode\t%s\n" "$mode"
printf "registered_count\t%s\n" "${#remove_registered[@]}"
printf "leftover_count\t%s\n" "${#remove_leftover[@]}"

run() {
	if [ "$mode" = dry-run ]; then
		printf "DRY\t%s\n" "$*"
	else
		printf "RUN\t%s\n" "$*"
		"$@"
	fi
}

if [ "${#target_registered[@]}" -gt 0 ]; then
	for wt in "${target_registered[@]}"; do
		if path_in_use "$wt"; then
			echo "refusing: $wt is a process cwd" >&2
			exit 1
		fi
		if [ "$mode" = apply ]; then
			in_porcelain "$wt" || {
				echo "refusing: $wt vanished from porcelain before remove" >&2
				exit 1
			}
			if path_in_use "$wt"; then
				echo "refusing: $wt is a process cwd at remove time" >&2
				exit 1
			fi
		fi
		run git -C "$repo" worktree remove --force "$wt"
		if [ "$mode" = apply ] && [ -e "$wt" ]; then
			printf "RUN\trm -rf surviving registered path %s\n" "$wt"
			rm -rf -- "$wt"
		fi
	done
fi

if [ "$mode" = apply ]; then
	run git -C "$repo" worktree prune
	classify_leftovers
	if [ "${#remove_leftover[@]}" -ne "$expect_leftover" ]; then
		echo "refusing: leftover_count after prune ${#remove_leftover[@]} != --expect-leftover $expect_leftover" >&2
		exit 1
	fi
else
	printf "DRY\tgit -C %s worktree prune\n" "$repo"
fi

if [ "${#target_leftover[@]}" -gt 0 ]; then
	for d in "${target_leftover[@]}"; do
		if [ "$mode" = apply ]; then
			is_leftover_clone "$d" "$repo" "$overlay" || {
				echo "refusing: $d is not a leftover clone at rm time" >&2
				exit 1
			}
			in_porcelain "$d" && {
				echo "refusing: $d is now in porcelain" >&2
				exit 1
			}
			if path_in_use "$d"; then
				echo "refusing: leftover $d is a process cwd at rm time" >&2
				exit 1
			fi
			printf "RUN\trm -rf -- %s\n" "$d"
			rm -rf -- "$d"
		else
			if path_in_use "$d"; then
				echo "refusing: leftover $d is a process cwd" >&2
				exit 1
			fi
			printf "DRY\trm -rf -- %s\n" "$d"
		fi
	done
fi
