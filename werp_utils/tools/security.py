###################################################################################
# 
#    Copyright (C) 2018 WERP IT GmbH
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################

import string
import random
import logging

_logger = logging.getLogger(__name__)

UNICODE_ASCII_CHARACTERS = string.ascii_letters + string.digits

#----------------------------------------------------------
# Generator
#----------------------------------------------------------

def generate_token(length=30, chars=UNICODE_ASCII_CHARACTERS):
    generator = random.SystemRandom()
    return "".join(generator.choice(chars) for index in range(length))