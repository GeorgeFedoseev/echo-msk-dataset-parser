import os


from pocketsphinx.pocketsphinx import *
from sphinxbase.sphinxbase import *


curr_dir_path = os.path.dirname(os.path.relpath(__file__))

model_path = os.path.join(curr_dir_path, "pocket_sphinx_model_ru")
#model_path = os.path.join(curr_dir_path, "pocket_sphinx_model_ru_2")


# config = {
#     'hmm': os.path.join(model_path, 'zero_ru.cd_cont_4000'),
#     'lm': os.path.join(model_path, 'ru.lm'),
#     'dict': os.path.join(model_path, 'ru.dic'),
#     'verbose': True,
#     'sampling_rate': 8000,
# }

config = Decoder.default_config()
config.set_string('-hmm',  os.path.join(model_path, 'zero_ru.cd_cont_4000/'))
#config.set_string('-hmm',  model_path)
config.set_string('-lm', os.path.join(model_path, 'ru.lm'))
config.set_string('-dict', os.path.join(model_path, 'ru.dic'))
config.set_string('-logfn', 'sphinx.log')
config.set_float('-samprate', 8000.)
config.set_boolean('-remove_noise', False)





print ('init...')
decoder = Decoder(config)

print ('decoding...')

frames = 0

out = []
stream = open(os.path.join(model_path, 'echo2.wav'), 'rb')
in_speech_bf = False
#decoder.reinit(config)
decoder.start_utt()
while True:
  buf = stream.read(1024)
  if buf:
      decoder.process_raw(buf, False, False)
      if decoder.get_in_speech() != in_speech_bf:
          in_speech_bf = decoder.get_in_speech()
          if not in_speech_bf:
              decoder.end_utt()
              out.append ((decoder.hyp().hypstr, list(decoder.seg())[0].start_frame, list(decoder.seg())[-1].end_frame))
              print (out[-1][0])
              decoder.start_utt()
  else:
      break

decoder.end_utt()