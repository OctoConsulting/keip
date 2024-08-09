set -eux

WEBHOOK_DIR=operator/webhook

verify_version_bump() {
  potential_tag=$(make --no-print-directory -C $WEBHOOK_DIR get-tag)
  sh .github/workflows/scripts/verify_changes_update_version.sh $potential_tag $WEBHOOK_DIR
}

verify_version_bump
