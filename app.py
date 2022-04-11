from flask import Flask, request
import requests
from twilio.twiml.messaging_response import MessagingResponse



app = Flask(__name__)


@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').lower()
    resp = MessagingResponse()
    msg = resp.message()
    responded = False

    if len(incoming_msg) == 7:
        print('digito ultimo: ' + (str(incoming_msg[6:7])))
        ultimo_digito = int(incoming_msg[6:7])
        if ultimo_digito >= 0 and ultimo_digito <= 9:
            print('ultimo digito si es numero ' + str(ultimo_digito))
            msg.body(darBaja(incoming_msg))
        else:
            msg.body('No corresponde a una placa')

        
        responded = True
    
    if len(incoming_msg) == 6:
        print('digito ultimo: ' + (str(incoming_msg[5:6])))
        msg.body(darBaja(incoming_msg))
        responded = True

    if not responded:
        msg.body('I only know about vehicle and motorcycle, sorry!')
    return str(resp)

       

def darBaja(incoming_msg):
    body = ''
    print('Placa a procesar: ' + incoming_msg)
    respInfoVeh = requests.get('http://192.168.1.194:4000/api/wsSao/getInfoVehiculo/1/'+ incoming_msg)
    if respInfoVeh.status_code == 200:
            data = respInfoVeh.json()
            codRetorno = data['codRetorno']
            if codRetorno == '0001':

                respFech = requests.get('http://192.168.1.119:10141/apiAMTZonaAzul_v1_00/Utiles/fechaSistema/*')  
                fechaData = respFech.json()
                fecha = str(fechaData['retorno']).replace("/","-")
                print('mod: ' + fecha)

                #retorno = f'{data["retorno"]["CodigoVehiculo"]}'
                codigoVehiculo = data["retorno"]["CodigoVehiculo"]
                respPagos = requests.get('http://192.168.1.194:4000/api/wsSao/getPagos/1/'+codigoVehiculo)
                #http://192.168.1.194:4000/api/wsSao/getPagos/1/3705562


                if respPagos.status_code == 200:
                    listData = respPagos.json()
                    codRetorno = listData['codRetorno']
                    if codRetorno == '0001':
                        ordenes = listData['retorno']['OrdenesPago']['OrdenPago']
                        contador = 0
                        for x in ordenes:
                            if x['DescripcionEstado'] == 'ACTIVO':
                                print(x['ID_OrdenPago'])
                                idOrden = x['ID_OrdenPago']
                                #print('http://192.168.1.194:4000/api/wsSao/bajaAutomaticaOrdenPago/'+str(idOrden)+'/'+str(fecha))
                                respBaja = requests.get('http://192.168.1.194:4000/api/wsSao/bajaAutomaticaOrdenPago/'+str(idOrden)+'/'+str(fecha))
                                if respBaja.status_code == 200:
                                    codRetorno = listData['codRetorno']
                                    if codRetorno == '0001':
                                        contador = contador + 1
                        body = 'Numero de ordenes procesadas: ' + str(contador)
                    else:
                        body = 'No se encontraron ordenes de pago'
                else:
                    body = 'No existe conexión consulta lista de ordenes'
            else:
                body = 'No existe la placa consultada o el vehiculo se encuentra bloqueado consultar AXIS-SRI'
    else:
            body = 'No existe conexión consulta vehiculo'
        

    return str(body)

if __name__ == '__main__':
    app.run()