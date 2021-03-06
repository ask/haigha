from haigha.frames import MethodFrame
from haigha.classes import ProtocolClass

class TransactionClass(ProtocolClass):
  '''
  Implements the AMQP Transaction class
  '''

  class TransactionsNotEnabled(ProtocolClass.ProtocolError): 
    '''Tried to use transactions without enabling them.'''

  def __init__(self, *args, **kwargs):
    super(TransactionClass, self).__init__(*args, **kwargs)
    self.dispatch_map = {
      11 : self._recv_select_ok,
      21 : self._recv_commit_ok,
      31 : self._recv_rollback_ok,
    }

    self._enabled = False
    self._commit_cb = []
    self._rollback_cb = []

  @property
  def enabled(self):
    '''Get whether transactions have been enabled.'''
    return self._enabled
  
  def select(self):
    '''
    Set this channel to use transactions.
    '''
    if not self._enabled:
      self._enabled = True
      self.send_frame( MethodFrame(self.channel_id, 90, 10) )
      self.channel.add_synchronous_cb( self._recv_select_ok )

  def _recv_select_ok(self, method_frame):
    # nothing to do
    pass
    
  def commit(self, cb=None):
    '''
    Commit the current transaction.  Caller can specify a callback to use
    when the transaction is committed.
    '''
    # Could call select() but spec 1.9.2.3 says to raise an exception
    if not self.enabled: raise TransactionsNotEnabled()

    self._commit_cb.append( cb )
    self.send_frame( MethodFrame(self.channel_id, 90, 20) )
    self.channel.add_synchronous_cb( self._recv_commit_ok )

  def _recv_commit_ok(self, method_frame):
    cb = self._commit_cb.pop(0)
    if cb is not None: cb()

  def rollback(self, cb=None):
    '''
    Abandon all message publications and acks in the current transaction.
    Caller can specify a callback to use when the transaction has been
    aborted.
    '''
    # Could call select() but spec 1.9.2.5 says to raise an exception
    if not self.enabled: raise TransactionsNotEnabled()

    self._rollback_cb.append( cb )
    self.send_frame( MethodFrame(self.channel_id, 90, 30) )
    self.channel.add_synchronous_cb( self._recv_rollback_ok )

  def _recv_rollback_ok(self, method_frame):
    cb = self._rollback_cb.pop(0)
    if cb is not None: cb()
