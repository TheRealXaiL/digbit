digbit
======

Automatic domain generation for BitSquatting

BitSquatting is not new but it's relatively new. This type of attack relies on a random bit that switches from 0 to 1 or from 1 to 0 inside a RAM. Because of this even though you try to access domain like cnn.com, in fact your computer is requesting ann.com. It's rare but it happens. It can be caused by a cosmic radiation or overheated memory modules. If You would like to learn more I can recommend [Artem's](http://dinaburg.org/bitsquatting.html) page.

To make it easier to find a domain that is in a single bit-shift distance (as in Hamming distance) I've created a script that is generating all the possibilities.

### Usage

```
usage: digbit.py [-h] [-r] [-o] [--update-tlds] [domain]

Generate bitsquatting domain variants (single bit-flip mutations).

positional arguments:
  domain          Target domain (e.g. example.com)

options:
  -h, --help      show this help message and exit
  -r, --resolve   Resolve each variant via DNS and show registration status
  -o, --original  Include the original domain in resolution output (requires -r)
  --update-tlds   Download the latest IANA TLD list and exit
```

### Examples

Generate bitsquat variants for a domain:

```bash
./src/digbit.py example.com
```

Resolve variants via DNS to check registration status:

```bash
./src/digbit.py -r example.com
```

```
DOMAIN       STATUS      IP
-----------  ----------  ---------------
uxample.com  REGISTERED  50.3.7.113
mxample.com  REGISTERED  78.31.70.110
axample.com  REGISTERED  157.90.33.74
gxample.com  AVAILABLE   -
dxample.com  AVAILABLE   -
...
```

Include the original domain in the output for comparison:

```bash
./src/digbit.py -r -o example.com
```

Update TLD cache from IANA (for accurate TLD filtering):

```bash
./src/digbit.py --update-tlds
```

### Features

- Generates all single-bit-flip domain variants
- Validates results against known TLDs (built-in set of ~70 common TLDs, or download the full IANA list with `--update-tlds`)
- RFC 1035 label validation (alphanumeric + hyphens, 1-63 chars)
- Deduplication and case normalization
- Integrated DNS resolution (no external tools needed)
- Clean pipe-friendly output (one domain per line without `-r`)

### Requirements

Python 3.6+. No external dependencies.
