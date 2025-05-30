# Verifies changes to directory have an updated version

if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: sh $0 <potential_git_tag> <path_to_directory> [extra_regex_excludes]"
  exit 1
fi

set -eu

POTENTIAL_GIT_TAG=$1
DIRECTORY=$2
ADDITIONAL_DIFF_IGNORE=${3:-}

GREP_FILTER_STDERR_OUTPUT="/tmp/diff_grep_filter_stderr"

main() {
  # github actions job does not fetch other git objects by default
  git fetch origin $GITHUB_BASE_REF
  git fetch --tags

  # if 'grep -v' (inverted-match) matches all the file-paths in the list, an error code is returned, which immediately
  # exits the script. This behavior is not desirable, since an empty list of diffs is valid in the context of
  # checking if a release is required. A '|| true' is added at the end of the command to force a non-error return code.
  # To still be able to catch any unexpected errors with the 'grep' command, stderr is piped to a file that is later
  # checked for errors.
  filtered_changes=$(git diff --name-only origin/$GITHUB_BASE_REF -- $DIRECTORY | grep -E -v \
                                                                            -e 'test/'  \
                                                                            -e 'requirements-dev\.txt$' \
                                                                            -e '\.md$' \
                                                                            $ADDITIONAL_DIFF_IGNORE \
                                                                            2> $GREP_FILTER_STDERR_OUTPUT \
                                                                            || true)

  if [ -s "$GREP_FILTER_STDERR_OUTPUT" ]; then
    echo "ERROR: failed to find changed files"
    cat $GREP_FILTER_STDERR_OUTPUT
    exit 1
  fi

  echo "Comparing current branch and $GITHUB_BASE_REF at directory: ${DIRECTORY}"

  if [ -n "$filtered_changes" ]; then
    echo "$filtered_changes"
    if git tag | grep -x "$POTENTIAL_GIT_TAG"; then
      echo "ERROR: $POTENTIAL_GIT_TAG was already released. Please increment the version if changes were made to $DIRECTORY."
      exit 1
    fi
    echo "Ready for release"
  else
    echo "Detected changes do not require a release"
  fi
}

main
