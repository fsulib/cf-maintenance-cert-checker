#!/bin/bash

function err_and_exit() {
    msg="${@}"
    echo "Error: ${msg}."
    echo "Exiting."
    exit 1
}

stack_name=${1:-Certificate-Checker}

[[ -f ${PWD}/check-certificates-deploy.yaml ]] || err_and_exit Can\'t locate the deployment template.
[[ -f ${PWD}/check-certificates-params.json ]] || err_and_exit Can\'t locate the parameters file.

function create_stack() {
    aws cloudformation create-stack \
        --stack-name "${stack_name}" \
        --template-body file://"${PWD}/check-certificates-deploy.yaml" \
        --parameters file://"${PWD}/check-certificates-params.json" \
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND
}

default="N"
read -n1 -r -p "Do you really want to launch Cert Checker stack (N/y)? " key
: ${key:=$default}

case "${key}" in
    'N')
        echo "Goodbye."
        exit 0
        ;;
    'y')
        echo ""
        create_stack
        exit $?
        ;;
esac
