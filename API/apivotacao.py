#coding: utf-8

import os
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
from base64 import b64decode
import json
import eleicao
from Crypto.Cipher import AES

NAME_APP = 'Eleições TSI'
passwd_criptografia = 'webservices-2018'

UPLOAD_FOLDER = './static/imagens'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



@app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE'])
def inicio():
    if request.method == 'GET':
        return render_template('index.html', nome=NAME_APP, paginaInicial=True)
    else:
        return json.dumps({'erro': 'Utilize o metodo GET para acessar essa páginas.'})



@app.route('/cadastro', methods=['GET'])
def paginaCadastro():
    return render_template('index.html', cadastrarCandidato=True, nome=NAME_APP)




@app.route('/listaCandidmethodsatos', methods=['GET'])
def lista():
    return render_template('index.html', nome=NAME_APP, listar=True, listaCandidatos=candidatos['candidatos'])




def calcularPorcentagem(votosCandidato, totalDeVotos):
    return float(votosCandidato * (totalDeVotos / 100))




@app.route('/apurarVotacao', methods=['GET'])
def apurarVotacao():
    ##candidatos = eleicao.apurar_votacao()

    totalDeVotos = 0

    candidatos = [{
                'numero': '17',
                'nome': 'Bolsonaro',
                'partido': 'PSL',
                'votos': '3',
            },
            {
                'numero': '13',
                'nome': 'Haddad',
                'partido': 'PT',
                'votos': '10',
            },
            {
                'numero': '12',
                'nome': 'Ciro',
                'partido': 'PDT',
                'votos': '22',
            }]

    for cand in candidatos:
        totalDeVotos += int(cand['votos'])

    for cand in candidatos:
        cand['porcentagem'] = calcularPorcentagem(int(cand['votos']), totalDeVotos)

    return render_template('index.html', nome=NAME_APP, apurar=True, listaCandidatos=candidatos)



@app.route('/candidato/<int:numero>', methods=['GET'])
def candidato(numero):
    dados = None
    try:
        dados = eleicao.checar_candidato(numero)
    except Exception as e:
        print(e)

    if not dados:
        return json.dumps({'nome': 'Não existe'})

    return json.dumps(dados)


def descriptografar(data):

    data = json.loads(data)
    print('data dict ', data, type(data))    

    data_cript = b64decode(data['data'].encode())
    nonce = b64decode(data['nonce'].encode())
    
    print('data cript', data_cript, type(data_cript))
    print('nonce', nonce, type(nonce))

    cripto = AES.new(passwd_criptografia.encode(), AES.MODE_EAX, nonce=nonce)
    data = cripto.decrypt(data_cript)
    print('data ', data, type(data))

    return data
    
    

@app.route('/voto/', methods=['GET'])
def vota(numero):
    try:
        data = descriptografar(request.text)

        if not eleicao.autenticar(data['passwd_blockchain']):
            raise Exception('Acesso a blockchain: Permissão negada!')

        status = eleicao.votar_candidato(data['voto'])
    except Exception as e:
        return json.dumps({'mensagem': 'Erro'})
        print(e)

    return json.dumps({'mensagem': 'Confirmado'})



# A partir do cadastro de um formulário, a API obtém os valores
# escolhidos pelo usuário, e a imagem do candidato.
# Retorna um json no formato abaixo
# {
#  'nome': 'Bulbassauro',
#  'numeroCandidato': 17,
#  'partido': 'PSL',
#  'imagem': 'Bulbassauro.png'
# }
@app.route('/cadastrar', methods=['GET','POST'])
def cadastrarCandidato():
    if request.method == 'POST':
        # Obtem o nome do candidato para salvar a imagem
        nomeCandidato = request.form['nomeCandidato']
        nCandidato = int(request.form['numCandidato'])

        # check if the post request has the file part
        if 'file' not in request.files:
            print('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            print('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Transforma o nome da imagem obtida para o nome do candidato
            nomeImagem = str(nCandidato) + '.' + filename.split('.')[1]
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], nomeImagem))

        candidato = {}
        candidato['nome'] = nomeCandidato
        candidato['numeroCandidato'] = nCandidato
        candidato['partido'] = request.form['partido']
        candidato['nome_imagem'] = nomeImagem

        candidatos['candidatos'].append(candidato)
        eleicao.cadastrar_candidato(nCandidato, nomeCandidato, candidato['partido'])
        return render_template('index.html', nome=NAME_APP, candidatoCadastrado = candidato)



@app.route('/apurar', methods=['GET','POST'])
def apurar():
    return json.dumps(eleicao.apurar_votacao())

if __name__ == '__main__':
    app.run(debug=True)
