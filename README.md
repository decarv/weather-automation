# weather-automation v0.1

Este repositório contém programas que coletam dados de tempo de websites,
armazenam esses dados e realizam o monitoramento da temperatura e da probabilidade de 
precipitação de datas passadas, de acordo com configuração realizada pelo programador.

As temperaturas coletadas e processadas são as temperaturas médias diárias e, por isso,
não existe motivo para a execução continuada do programa ao longo de um dia. O programador
deverá ajustar os parâmetros do programa para decidir em que horário cada programa rodará no dia.

## Funcionamento do Programa

O programa está dividido em dois processos. O primeiro, `Weather Scrapper`, carrega os dados de um
endpoint privado do weather.com e os salva em uma base de dados Postgresql. O segundo, `Weather Monitor`,
monitora as instâncias recentemente adicionadas na base de dados e envia um e-mail, a ser configurado pelo
programador.

## Configurando os Parâmetros

Toda a configuração do programa deve ser feita pelo arquivo `docker-compose.yml`, nos títulos `environment`. 
Para facilitar o trabalho do programador, o arquivo já está preenchido com alguns valores boilerplate.

As configurações que podem ser realizadas no monitor são:
```Dockerfile
    environment:
      SCHEDULE: 10:00
      SENDER_EMAIL: weather.monitor@outlook.com
      EMAIL_PASSWORD: weather.M0N1T0R
      RECEIVER_EMAIL: decarv.henrique@gmail.com
      SMTP_SERVER: smtp-mail.outlook.com
      SMTP_SERVER\_PORT: 587
      DB_CONNECTION_STRING: postgres://postgres:postgrespw@postgres:5432
      POSTGRES_PASSWORD: postgrespw
      TEMPERATURE_MIN: 10
      TEMPERATURE_MAX: 20
      PRECIPITATION_PROBABILITY_MIN: 50
```

As configurações que podem ser realizadas no scrapper são:
```Dockerfile
    environment:
      SCHEDULE: 11:00
      CITY: SAO PAULO
      DB_CONNECTION_STRING: postgres://postgres:postgrespw@postgres:5432
      SERVICE: weather.com
      POSTGRES_PASSWORD: postgrespw
```

O monitor só enviará e-mails para as datas em que as condições de temperatura média de um dia estiverem entre a temperatura mínima
definida (`TEMPERATURE_MIN`) e a temperatura máxima definida (`TEMPERATURE_MAX`) ou de um dia em que a probabilidade de precipitação
seja maior que a definida (`PRECIPITATION_PROBABILITY_MIN`).

## Instalação

Para instalar os programas, basta montar as imagens do weather-scrapper e weather-monitor, rodando os comandos
de dentro do diretório do repositório clonado:

```bash
$ docker build -t weather-scrapper -f .\scrapper\Dockerfile .
$ docker build -t weather-monitor -f .\monitor\Dockerfile .
```

Em seguida, rodar, do mesmo diretório, o comando:

 ```bash
$ docker compose up
```

## Autor

Henrique de Carvalho
