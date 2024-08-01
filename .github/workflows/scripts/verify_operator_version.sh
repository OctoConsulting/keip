set -eux

OPERATOR_DIR=operator
OPERATOR_CONTROLLER_YAML=$OPERATOR_DIR/controller/integrationroute-controller.yaml

verify_current_webhook_img() {
  current_webhook_img=$(make --no-print-directory -C operator/webhook get-image-name)
  webhook_image_used=$(yq eval '.spec.template.spec.containers[].image' $OPERATOR_CONTROLLER_YAML)

  test -n "$current_webhook_img"
  test -n "$webhook_image_used"

  test "$webhook_image_used" = "$current_webhook_img"
}

verify_operator_version_bump() {
  # github actions job does not fetch other git objects by default
  git fetch origin $GITHUB_BASE_REF
  git fetch --tags

  changes_in_pr=$(git diff origin/$GITHUB_BASE_REF -- $OPERATOR_DIR)
  if [ -n "$changes_in_pr" ]; then
    echo "Found changes between current branch and $GITHUB_BASE_REF"
    potential_tag=$(make --no-print-directory -C $OPERATOR_DIR get-tag)
    if git tag | grep -x "$potential_tag"; then
      echo "$potential_tag was already released. Please increment the version if changes were made to the operator."
      exit 1
    fi
  fi
}

verify_current_webhook_img
verify_operator_version_bump
