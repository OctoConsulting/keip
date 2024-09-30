set -eux

OPERATOR_DIR=operator

verify_version_bump() {
  potential_tag=$(make --no-print-directory -C $OPERATOR_DIR get-tag)
  sh .github/workflows/scripts/shared/verify_changes_update_version.sh $potential_tag $OPERATOR_DIR
}

sh .github/workflows/scripts/shared/verify_current_webhook_img.sh
verify_version_bump
