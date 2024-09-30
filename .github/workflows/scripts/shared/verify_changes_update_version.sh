# Verifies changes to directory have an updated version

if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: sh $0 [potential_git_tag] <path_to_directory>"
  exit 1
fi

set -eux

POTENTIAL_GIT_TAG=$1
DIRECTORY=$2

main() {
  # github actions job does not fetch other git objects by default
  git fetch origin $GITHUB_BASE_REF
  git fetch --tags

  changes_in_pr=$(git diff origin/$GITHUB_BASE_REF -- $DIRECTORY)
  if [ -n "$changes_in_pr" ]; then
    echo "Found changes between current branch and $GITHUB_BASE_REF"
    if git tag | grep -x "$POTENTIAL_GIT_TAG"; then
      echo "$POTENTIAL_GIT_TAG was already released. Please increment the version if changes were made to $DIRECTORY."
      exit 1
    fi
  fi
}

main
