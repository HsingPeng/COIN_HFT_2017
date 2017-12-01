import abc

class Exchange:
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.__depth_dict = dict()

    def get_depth_dict(self):
        return self.__depth_dict

    def _update_depth(self, base_coin, trans_coin, bids_list, asks_list):
        base_coin_dict = self.__depth_dict.get(base_coin);
        if base_coin_dict == None:
            base_coin_dict = dict()
            self.__depth_dict[base_coin] = base_coin_dict
        trans_coin_dict = base_coin_dict.get(trans_coin);
        if trans_coin_dict == None:
            trans_coin_dict = dict()
            base_coin_dict[trans_coin] = trans_coin_dict
        trans_coin_dict.clear()
        trans_coin_dict['bids'] = bids_list
        trans_coin_dict['asks'] = asks_list

    def get_depth(self, base_coin, trans_coin, bids_or_asks):
        base_coin_dict = __depth_dict.get(base_coin)
        if base_coin_dict != None:
            trans_coin_dict = base_coin_dict.get(trans_coin);
            if trans_coin_dict != None:
                bids_or_asks_list = trans_coin_dict.get(bids_or_asks)
                if (bids_or_asks_list == None):
                    return None
        return tuple(bids_or_asks_list)
    
    @abc.abstractmethod
    def connect(self):
        pass

    @abc.abstractmethod
    def close(self):
        pass
