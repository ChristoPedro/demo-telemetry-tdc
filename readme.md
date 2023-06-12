# Demo - OpenTelemetry

Objetivo é criar um ambiente com exemplo da utilização de OpenTelemetry para a instrumentação e monitoramento de aplicações.

- [Demo - OpenTelemetry](#demo---opentelemetry)
  - [Arquitetura](#arquitetura)
  - [Pré-Requisitos](#pré-requisitos)
  - [Setup Kubernetes](#setup-kubernetes)
    - [Dando permissão de Intance Principal para os nós de Kubernetes](#dando-permissão-de-intance-principal-para-os-nós-de-kubernetes)
    - [ConfigMaps](#configmaps)
    - [OpenTelemetry](#opentelemetry)
    - [Deploy da Aplicação](#deploy-da-aplicação)


## Arquitetura

![Arquitetura](/images/TDC.png)

## Pré-Requisitos

- [Criar uma Conta](https://www.oracle.com/br/cloud/free/) na Oracle Cloud 
- [Criar um Compartment](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingcompartments.htm)
- [Criar um kubernetes](https://docs.oracle.com/en/solutions/build-rest-java-application-with-oke/configure-your-kubernetes-cluster-oracle-cloud1.html#GUID-D1832637-FFF9-4875-9408-4F28320511E1) (OKE) na Oracle Cloud
- [Criar um banco MySQL](https://blogs.oracle.com/developers/post/complete-guide-to-getting-started-with-mysql-db-in-the-oracle-cloud)
- [Criar um Vault e um Secret](https://docs.oracle.com/en/database/other-databases/essbase/19.3/essad/create-vault-secrets-and-encrypt-values.html#:~:text=Sign%20in%20to%20the%20Oracle,Click%20Create%20Vault.) para armazenar a senha do Banco de Dados
- [Criar um OCI Queue](https://docs.oracle.com/en-us/iaas/Content/queue/queue-create.htm)
- [Criar um APM Domain](https://docs.oracle.com/en-us/iaas/application-performance-monitoring/doc/create-apm-domain.html)

## Setup Kubernetes

- Instalar Cert Manager: 

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.12.0/cert-manager.yaml
```

- Instalar OpenTelemetry Kubernetes Operator:

```bash 
kubectl apply -f https://github.com/open-telemetry/opentelemetry-operator/releases/latest/download/opentelemetry-operator.yaml
```

### Dando permissão de Intance Principal para os nós de Kubernetes

Para saber mais sobre Intance Principal acesse a [documentação](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/callingservicesfrominstances.htm)

Crie um Dynamic Group com a seguinte regra.

```
instance.compartment.id = '<compartment_ocid>'
```
- **compartment_ocid** compartimento onde foi criado o Cluster de Kubernetes

Depois crie uma [política](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/callingservicesfrominstances.htm) que permite que o Dynamic Group possa utilizar os recursos do compartimento.

```
Allow dynamic-group <dynamic_group_name> to manage all-resources in <compartment-name>
```

- **dynamic_group_name** nome do dynamic gourp criado anteriormente.
- **compartment-name** nome do compartimento onde o kubernetes foi criado.

### ConfigMaps

[Aqui](/manifestos/config-maps.yaml) temos os ConfigMaps utilizados pela aplicação de Demo. Precisamos substituir as seguintes variáveis.

  - **queue_endpoint**: Endpoint do serviço de OCI Queue encontrado na Console do serviço
  - **queue_ocid**: OCID do serviço de OCI Queue encontrado na Console do serviço
  - **secret_ocid**: OCID do Sercret criado anteriormente para armazenar a senha do MySQL
  - **msql_host**: IP do serviço de MySQL criado anteriormente
  - **mysql_user**: Usuário do serivo de MySQL

Após a alteração das variáveis de ambiente, execute o comando abaixo para criar os ConfigMaps no cluster de Kubernetes.

```bash
kubectl apply -f config-maps.yaml
```

### OpenTelemetry

Para configurar o Collector e a Instrumentação automática no [aquivo](/manifestos/otel-configuration.yaml) de manifesto do OpenTelemetry substitua as seguites variáveis:

- **apm_endpoint** Endpoint do domínio do APM criado anteriormente
- **private_date_key** Private Key do domínio do APM criado anteriomente

E crie os artefatos no cluster:

```bash
kubectl apply -f otel-configuration.yaml
```

### Deploy da Aplicação

Crie os artefatos da aplicação no Kubernetes com o seguinte comando:

```bash
kubectl apply -f deployapp.yaml
```
