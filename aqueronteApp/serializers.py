# Convierte los datos guardados en los modelos en JSON.
# ejemplo:
# serializer = TickeSerializer(someTicket)
# serializer.data
# {'token': 'exampleticket12345', 'roberto': 'robertez', '1-9'}

from rest_framework import serializers

from aqueronteApp.models import Tickets, Usuarios


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuarios
        fields = ('rut', 'nombres', 'apellidos')


class TicketSerializer(serializers.ModelSerializer):
    usuario = UserSerializer(required=True)

    class Meta:
        model = Tickets
        fields = ('ticket', 'valid', 'usuario')
        # depth = 4

    def create(self, validated_data):
        """
        Overriding the default create method of the Model serializer.
        :param validated_data: data containing all the details of student
        :return: returns a successfully created student record
        """
        print("CREATE")
        user_data = validated_data.pop('info')
        print("user_data", user_data)
        usuario = UserSerializer.create(UserSerializer(), validated_data=user_data)
        ticket = Tickets.objects.update_or_create(ticket=validated_data.pop('ticket'), valid=validated_data.pop('valid'),
                                                  usuario=usuario)
        return ticket
