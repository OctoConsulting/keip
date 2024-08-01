set -eux

OPERATOR_CONTROLLER_YAML=operator/controller/integrationroute-controller.yaml

install_dependencies() {
  # install yq
  echo installing
}

verify_current_webhook_img() {
  current_webhook_img=$(make --no-print-directory -C operator/webhook get-image-name)
  webhook_image_used=$(yq eval '.spec.template.spec.containers[].image' $OPERATOR_CONTROLLER_YAML)

  test "$webhook_image_used" = "$current_webhook_img"
}

install_dependencies
verify_current_webhook_img
