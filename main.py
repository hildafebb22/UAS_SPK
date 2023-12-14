from http import HTTPStatus
from flask import Flask, request, abort
from flask_restful import Resource, Api 
from models import Handphone as handphoneModel
from engine import engine
from sqlalchemy import select
from sqlalchemy.orm import Session
from tabulate import tabulate

session = Session(engine)

app = Flask(__name__)
api = Api(app)        

class BaseMethod():

    def __init__(self):
        self.raw_weight = {'kamera': 3, 'ram': 4, 'baterai': 4, 'harga': 3, 'ukuranlayar': 3}

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v/total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(handphoneModel.id, handphoneModel.kamera, handphoneModel.ram, handphoneModel.baterai, handphoneModel.harga, handphoneModel.ukuranlayar)
        result = session.execute(query).fetchall()
        print(result)
        return [{'id': Handphone.id, 'kamera': Handphone.kamera, 'ram': Handphone.ram, 'baterai': Handphone.baterai, 'harga': Handphone.harga, 'ukuranlayar': Handphone.ukuranlayar} for Handphone in result]

    @property
    def normalized_data(self):
        kamera_values = []
        ram_values = []
        baterai_values = []
        harga_values = []
        ukuranlayar_values = []

        for data in self.data:
            kamera_values.append(data['kamera'])
            ram_values.append(data['ram'])
            baterai_values.append(data['baterai'])
            harga_values.append(data['harga'])
            ukuranlayar_values.append(data['ukuranlayar'])

        return [
            {'id': data['id'],
             'kamera': data['kamera'] / max(kamera_values),
             'ram': data['ram'] / max(ram_values),
             'baterai': data['baterai'] / max(baterai_values),
             'harga': min(harga_values) / data['harga'] if data['harga'] != 0 else 0,
             'ukuranlayar': data['ukuranlayar'] / max(ukuranlayar_values)
             }
            for data in self.data
        ]

    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class WeightedProductCalculator(BaseMethod):
    def update_weights(self, new_weights):
        self.raw_weight = new_weights

    @property
    def calculate(self):
        normalized_data = self.normalized_data
        produk = [
            {
                'id': row['id'],
                'produk': row['kamera'] ** self.raw_weight['kamera'] *
                row['ram'] ** self.raw_weight['ram'] *
                row['baterai'] ** self.raw_weight['baterai'] *
                row['harga'] ** self.raw_weight['harga'] *
                row['ukuranlayar'] ** self.raw_weight['ukuranlayar']
            }
            for row in normalized_data
        ]
        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)
        sorted_data = [
            {
                'ID': product['id'],
                'score': round(product['produk'], 5)
            }
            for product in sorted_produk
        ]
        return sorted_data


class WeightedProduct(Resource):
    def get(self):
        calculator = WeightedProductCalculator()
        result = calculator.calculate
        return result, HTTPStatus.OK.value
    
    def post(self):
        new_weights = request.get_json()
        calculator = WeightedProductCalculator()
        calculator.update_weights(new_weights)
        result = calculator.calculate
        return {'Handphone': result}, HTTPStatus.OK.value
    

class SimpleAdditiveWeightingCalculator(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = [
            {
                'id':row['id'],
                'Score':round(row['kamera'] * weight['harga'] +
                        row['ram'] * weight['ram'] +
                        row['baterai'] * weight['baterai'] +
                        row['harga'] * weight['harga'] +
                        row['ukuranlayar'] * weight['ukuranlayar'], 5)
            }
            for row in self.normalized_data
        ]
        sorted_result = sorted(result, key=lambda x: x['Score'], reverse=True)
        return sorted_result


    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class SimpleAdditiveWeighting(Resource):
    def get(self):
        saw = SimpleAdditiveWeightingCalculator()
        result = saw.calculate
        return sorted(result, key=lambda x: x['Score'], reverse=True), HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        saw = SimpleAdditiveWeightingCalculator()
        saw.update_weights(new_weights)
        result = saw.calculate
        return {'Handphone': sorted(result, key=lambda x: x['Score'], reverse=True)}, HTTPStatus.OK.value



class Handphone(Resource):
    def get_paginated_result(self, url, list, args):
        page_size = int(args.get('page_size', 10))
        page = int(args.get('page', 1))
        page_count = int((len(list) + page_size - 1) / page_size)
        start = (page - 1) * page_size
        end = min(start + page_size, len(list))

        if page < page_count:
            next_page = f'{url}?page={page+1}&page_size={page_size}'
        else:
            next_page = None
        if page > 1:
            prev_page = f'{url}?page={page-1}&page_size={page_size}'
        else:
            prev_page = None
        
        if page > page_count or page < 1:
            abort(404, description=f'Halaman {page} tidak ditemukan.') 
        return {
            'page': page, 
            'page_size': page_size,
            'next': next_page, 
            'prev': prev_page,
            'Results': list[start:end]
        }

    def get(self):
        query = select(handphoneModel)
        data = [{'id': Handphone.id, 'kamera': Handphone.kamera, 'ram': Handphone.ram, 'baterai': Handphone.baterai, 'harga': Handphone.harga, 'ukuranlayar': Handphone.ukuranlayar} for Handphone in session.scalars(query)]
        return self.get_paginated_result('handphone/', data, request.args), HTTPStatus.OK.value


api.add_resource(Handphone, '/handphone')
api.add_resource(WeightedProduct, '/wp')
api.add_resource(SimpleAdditiveWeighting, '/saw')

if __name__ == '__main__':
    app.run(port='5005', debug=True)
