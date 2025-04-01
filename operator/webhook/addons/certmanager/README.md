# Certmanager Addon

The Certmanager Addon creates certificates for `IntegrationRoute`s based off of annotations in the `IntegrationRoute`.

See the example `IntegrationRoute` in the [README](../../../example/README.md#example-integrationroute-using-tls-and-the-certmanager-addon).

## Supported Annotations
- **cert-manager.io/issuer:** The name of an `Issuer` to acquire the `Certificate` required for this `IntegrationRoute`. The `Issuer` must be in the same namespace as the `IntegrationRoute` resource.
- **cert-manager.io/cluster-issuer:** The name of a `ClusterIssuer` to acquire the `Certificate` required for this `IntegrationRoute`. It does not matter which namespace your `IntegrationRoute` resides, as `ClusterIssuer`s are non-namespaced resources.
- **cert-manager.io/common-name:** (optional) This annotation allows you to configure `spec.commonName` for the `Certificate` to be generated.
- **cert-manager.io/subject-countries:** (optional) This annotation allows you to configure the `spec.subject.countries` field for the `Certificate` to be generated. Supports comma-separated values e.g. "Country 1,Country 2".
- **cert-manager.io/subject-localities:** (optional) This annotation allows you to configure the `spec.subject.localities` field for the `Certificate` to be generated. Supports comma-separated values e.g. "City 1,City 2".
- **cert-manager.io/subject-provinces:** (optional) This annotation allows you to configure the `spec.subject.provinces` field for the `Certificate` to be generated. Supports comma-separated values e.g. "Province 1,Province 2".
- **cert-manager.io/subject-organizationalunits:** (optional) This annotation allows you to configure the `spec.subject.organizationalUnits` field for the `Certificate` to be generated. Supports comma-separated values e.g. "IT Services,Cloud Services".
- **cert-manager.io/alt-names:** (optional) This annotation allows you to configure subject alternative names (SANs). Supports comma-separated values e.g. "san1,san2".

> **_NOTE:_**  `IntegrationRoute`s cannot have both `cert-manager.io/issuer` and `cert-manager.io/cluster-issuer` annotations.

## See Also
- [Cert-manager.io Supported Annotations](https://cert-manager.io/docs/usage/ingress/#supported-annotations)
