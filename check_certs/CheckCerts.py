import boto3
import os
from datetime import datetime

class CertCheckException(Exception):
    """A custom exception to call if check_certs borks.
    """
    pass

def check_certs(event, context):
    """This function retrieves the 'NotAfter' dates from certificates held in 
    Amazon Certificate Manager and notifies an SNS topic:
        1. if any of them are nearing their expiration dates (audit var)
        2. a full report of all certs remaining time (report var)
        3. both of the above.

    Environment:
    region -- the region hosting our certs.
    snsAuditArn -- the arn of the SNS topic to notify if certs' remaining 
                   life is below the days threshold.
    snsReportArn -- the arn of the SNS topic to notify if simply reporting
                    our certs' remaining time of validity.
    days -- the NotAfter threshold
    audit -- a Yes/No (not a bool!) specifying to run an audit.
    report -- a Yes/No (not a bool!) to run a report

    Positional Arguments:
    event -- the event passed to the lambda function by the caller
    context -- the context in which the function runs
    """
    try:
        region = os.environ.get("region", default='us-east-1')
        days = os.environ.get("daysThreshold", default="30")
        do_audit = os.environ.get("doAudit", default="True")
        do_report = os.environ.get("doReport", default="False")
        env_vars = [region, days]
        if ("Yes" in do_audit):
            sns_audit_arn = os.environ.get("snsAuditArn", default=None)
            env_vars.append(sns_audit_arn)
        if ("Yes" in do_report):
            sns_report_arn = os.environ.get("snsReportArn", default=None)
            env_vars.append(sns_report_arn)
        if (None in env_vars):
            raise Exception
    except Exception:
        raise CertCheckException("A required environment variable is either "
                                 "unset or None.")

    try:
        acm_client = boto3.client('acm', region_name=region)
        cert_summaries = acm_client.list_certificates(
                CertificateStatuses=['ISSUED']
                )

        cert_descriptions = []
        for summary in cert_summaries['CertificateSummaryList']:
            cert_descriptions.append(
                acm_client.describe_certificate(
                    CertificateArn=summary['CertificateArn']
                    )
                )

        now_tzaware = datetime.now(tz=datetime.utcnow().astimezone().tzinfo)
        days_until_expiry = []
        for description in cert_descriptions:
            domain_name = description['Certificate']['DomainName']
            days_left = (description['Certificate']['NotAfter'] - now_tzaware).days
            days_until_expiry.append({
                "DomainName": domain_name,
                "DaysLeft": days_left
                })

    except Exception as e:
        raise CertCheckException("Something went wrong gathering a cert "
                                 "expiration list: {}".format(e))

    if ("Yes" in do_audit):
        try:
            fewer_days_than_thresh = [ x for x in days_until_expiry if x['DaysLeft'] <= int(days) ]
            if len(fewer_days_than_thresh):
                exp_strings = ["{: <36} is valid for {} more days".format(x['DomainName'],
                    x['DaysLeft']) for x in fewer_days_than_thresh]
                message=("The following certificates will expire within {} days:\n\n"
                         "{}".format(days, "\n".join(exp_strings))
                         )
                send_notification(message=message,
                        topic=sns_audit_arn,
                        subject="Warning: Certificate Expiration",
                        region=region)
        except Exception as e:
            raise CertCheckException("Something went wrong while doing the "
                                     "certificate audit: {}".format(e))

    if ("Yes" in do_report):
        try:
            report_string = ["{: <36}: valid for {} days.".format(x['DomainName'],
                x['DaysLeft']) for x in days_until_expiry]
            message=("Certificate expiration report:\n\n"
                     "{}".format("\n".join(report_string))
                     )
            send_notification(message=message,
                    topic=sns_report_arn,
                    subject="Notice: Certificate Expiration Report",
                    region=region)
        except Exception as e:
            raise CertCheckException("Something went wrong while reporting "
                                     "certificate expiration dates: {}".format(e))

def send_notification(message=None, topic=None, subject=None, region='us-east-1'):
    """Sends the SNS notification.
    """
    try:
        sns_client = boto3.client('sns', region_name=region)
        sns_client.publish(
                TopicArn=topic,
                Message=message,
                Subject=subject)
    except Exception as e:
        raise CertCheckException("Something went wrong while notifying the "
                                 "certificate check topic(s): {}".format(e))

