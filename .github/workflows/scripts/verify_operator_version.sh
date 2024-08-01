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

  # fetch because job does not fetch other branches by default
  git fetch origin $GITHUB_BASE_REF

  changes_in_pr=$(git diff origin/$GITHUB_BASE_REF -- $OPERATOR_DIR)
  if [ -z "$changes_in_pr" ]; then
    echo "found operator changes"
  fi

  changes_in_pr=$(git diff origin/$GITHUB_BASE_REF -- keip-container-archetype)
    if [ -z "$changes_in_pr" ]; then
      echo "found archetype changes"
    fi
}

verify_current_webhook_img
verify_operator_version_bump
