set -eux

WEBHOOK_DIR=operator/webhook

verify_version_bump() {
  potential_tag=$(make --no-print-directory -C $WEBHOOK_DIR get-tag)
  sh .github/workflows/scripts/shared/verify_changes_update_version.sh $potential_tag $WEBHOOK_DIR
}

sh .github/workflows/scripts/shared/verify_current_webhook_img.sh
verify_version_bump
