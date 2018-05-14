# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

import signalupdate_pb2 as signalupdate__pb2


class GreeterStub(object):
  # missing associated documentation comment in .proto file
  pass

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.SignalUpdate = channel.unary_unary(
        '/helloworld.Greeter/SignalUpdate',
        request_serializer=signalupdate__pb2.UpdateRequest.SerializeToString,
        response_deserializer=signalupdate__pb2.UpdateReply.FromString,
        )


class GreeterServicer(object):
  # missing associated documentation comment in .proto file
  pass

  def SignalUpdate(self, request, context):
    """Sends a greeting
    """
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_GreeterServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'SignalUpdate': grpc.unary_unary_rpc_method_handler(
          servicer.SignalUpdate,
          request_deserializer=signalupdate__pb2.UpdateRequest.FromString,
          response_serializer=signalupdate__pb2.UpdateReply.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'helloworld.Greeter', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))