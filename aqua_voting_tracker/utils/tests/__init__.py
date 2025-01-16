import factory
import faker

from aqua_voting_tracker.utils.stellar.fake import StellarProvider


fake = faker.Faker()
fake.add_provider(StellarProvider)


factory.Faker.add_provider(StellarProvider)
