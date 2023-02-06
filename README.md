# weather-automation v0.1

Este reposit�rio cont�m programas que coletam dados de tempo de websites,
armazenam esses dados e realizam o monitoramento da temperatura e da probabilidade de 
precipita��o de datas passadas, de acordo com configura��o realizada pelo programador.

As temperaturas coletadas e processadas s�o as temperaturas m�dias di�rias e, por isso,
n�o existe motivo para a execu��o continuada do programa ao longo de um dia. O programador
dever� ajustar os par�metros do programa para decidir em que hor�rio cada programa rodar� no dia.

## Funcionamento do Programa

O programa est� dividido em dois processos. O primeiro, `Weather Scrapper`, carrega os dados de um
endpoint privado do weather.com e os salva em uma base de dados Postgresql. O segundo, `Weather Monitor`,
monitora as inst�ncias recentemente adicionadas na base de dados e envia um e-mail, a ser configurado pelo
programador.

## Configurando os Par�metros

Toda a configura��o do programa deve ser feita pelo arquivo `docker-compose.yml`, nos t�tulos `environment`. 
Para facilitar o trabalho do programador, o arquivo j� est� preenchido com alguns valores boilerplate.

As configura��es que podem ser realizadas no monitor s�o:
```Dockerfile
    environment:
      SCHEDULE: 10:00
      SENDER\_EMAIL: weather.monitor@outlook.com
      EMAIL\_PASSWORD: weather.M0N1T0R
      RECEIVER\_EMAIL: decarv.henrique@gmail.com
      SMTP\_SERVER: smtp-mail.outlook.com
      SMTP\_SERVER\_PORT: 587
      DB\_CONNECTION_STRING: postgres://postgres:postgrespw@postgres:5432
      POSTGRES\_PASSWORD: postgrespw
      TEMPERATURE\_MIN: 10
      TEMPERATURE\_MAX: 20
      PRECIPITATION\_PROBABILITY\_MIN: 50
```

As configura��es que podem ser realizadas no scrapper s�o:
```Dockerfile
    environment:
      SCHEDULE: 11:00
      CITY: SAO PAULO
      DB\_CONNECTION_STRING: postgres://postgres:postgrespw@postgres:5432
      SERVICE: weather.com
      POSTGRES\_PASSWORD: postgrespw
```

O monitor s� enviar� e-mails para as datas em que as condi��es de temperatura m�dia de um dia estiverem entre a temperatura m�nima
definida (`TEMPERATURE_MIN`) e a temperatura m�xima definida (`TEMPERATURE_MAX`) ou de um dia em que a probabilidade de precipita��o
seja maior que a definida (`PRECIPITATION_PROBABILITY_MIN`).

## Instala��o

Para instalar os programas, basta montar as imagens do weather-scrapper e weather-monitor, rodando os comandos
de dentro do diret�rio do reposit�rio clonado:

```bash
$ docker build -t weather-scrapper -f .\scrapper\Dockerfile .
$ docker build -t weather-monitor -f .\monitor\Dockerfile .
```

Em seguida, rodar, do mesmo diret�rio, o comando:

 ```bash
$ docker compose up
```

## Autor

Henrique de Carvalho
