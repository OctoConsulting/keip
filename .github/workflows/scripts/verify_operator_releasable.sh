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

verify_version_bump() {
  potential_tag=$(make --no-print-directory -C $OPERATOR_DIR get-tag)
  sh .github/workflows/scripts/verify_changes_update_version.sh $potential_tag $OPERATOR_DIR
}

verify_current_webhook_img
verify_version_bump
