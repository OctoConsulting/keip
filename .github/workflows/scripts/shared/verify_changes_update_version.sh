# Verifies changes to directory have an updated version

if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: sh $0 [potential_git_tag] <path_to_directory>"
  exit 1
fi

set -eu

POTENTIAL_GIT_TAG=$1
DIRECTORY=$2
ADDITIONAL_DIFF_IGNORE=${3:-}

main() {
  # github actions job does not fetch other git objects by default
  git fetch origin $GITHUB_BASE_REF
  git fetch --tags

  filtered_changes=$(git diff --name-only origin/$GITHUB_BASE_REF -- $DIRECTORY | grep -E -v \
                                                                            -e 'test/'  \
                                                                            -e 'requirements-dev\.txt$' \
                                                                            -e '\.md$' \
                                                                            $ADDITIONAL_DIFF_IGNORE)

  if [ -n "$filtered_changes" ]; then
    echo "Found changes between current branch and $GITHUB_BASE_REF"
    echo "$filtered_changes"
    if git tag | grep -x "$POTENTIAL_GIT_TAG"; then
      echo "$POTENTIAL_GIT_TAG was already released. Please increment the version if changes were made to $DIRECTORY."
      exit 1
    fi
  fi
}

main
