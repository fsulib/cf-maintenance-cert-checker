This stack that launches two scheduled lambdas that check certificates in Amazon Certificate Manager. AWS does not remind its users of upcoming expirations of third-party certs.

CertAuditRunner provides a bi-weekly check for any certs that will expire within 30 days.

CertReportRunner provides a quarterly report of all certs and their remaining lifespans.

Supply parameters to adjust job run frequency, the trigger threshold for expiration warnings, and whether to run either, both, or neither function.

You absolutely must supply an email address for notifications.
