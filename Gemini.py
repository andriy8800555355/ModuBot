from g4f.client import Client
from g4f.cookies import set_cookies

set_cookies(".google.com", {
  "__Secure-1PSID": "g.a000kQhc4aMR8aP7KEcKsy-tErsu8MZt1STk0pdhekcl2AF7IvaseR0rsgDbkhwlwjyozZHLVQACgYKAVASAQASFQHGX2Mi488KyMl7WiQ6o2VUS---8BoVAUF8yKoKLsmBmeqqXN4HtyE2o9420076"
})

client = Client()
response = client.images.generate(
  model="gemini",
  prompt="a white siamese cat",
)

image_url = response.data[0].url