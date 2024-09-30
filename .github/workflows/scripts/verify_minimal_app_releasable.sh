set -eux

MINIMAL_APP_DIR=minimal-app

verify_version_bump() {
  version=$(mvn -f minimal-app/pom.xml help:evaluate -Dexpression=project.version -q -DforceStdout)
  potential_tag="${GIT_TAG_PREFIX}${version}"
  sh .github/workflows/scripts/shared/verify_changes_update_version.sh $potential_tag $MINIMAL_APP_DIR
}

verify_version_bump
