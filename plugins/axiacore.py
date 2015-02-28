from will.plugin import WillPlugin
from will.decorators import respond_to, periodic, hear, randomly, route, rendered_template, require_settings


class AxiaCorePlugin(WillPlugin):

    @hear("what do you think")
    def tell_what_i_think(self, message):
        url = 'https://s3.amazonaws.com/uploads.hipchat.com/50553/341552/g7rcdoer2w1Kv5X/miguel-approves.png'
        self.say(url, message=message)
