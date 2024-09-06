# konkordans

Gå til https://mybinder.org/v2/gh/Yoonsen/NAOB_konkordans/master for å sjekke ut.

## Publiser appen 

```shell
python ./naob2gcp.py 
```

Dette scriptet gjør flere ting: 
- Lager deployment.yaml for appen på GCP 
- kjører kubectl apply 
- Oppretter en k8s service 
- Oppretter en ingress.yaml 
- Oppretter en Dockerfile

