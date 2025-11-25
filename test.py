import tweepy

bearerToken = "AAAAAAAAAAAAAAAAAAAAACWF5gEAAAAAwEPHNogLL0WvwU8vDHC2LeCBejo%3DdjIWRjPvHDPMkO3tLGRaxuwQkMMULZM6lAJudQOSBLex1sbiM0"
apiKey = "YkljsGq2HJgelxIz6pNxFV2ZK"
apiSecret = "1xFQk05BQMMmrd3PPqSzZ3z20yHmsVZrCX2XXFkeIxoAzGO0II"
accessToken = "1186022699493154816-yDoWhKDRKdnGMfh9ivNHMa824LCnlg"
accessTokenSecret = "0iXFRk1ZNC3f6kMg2uE8Ng5lhSEuXBUFOzKRHqduwYOjh"

auth = tweepy.OAuth1UserHandler(apiKey, apiSecret, accessToken, accessTokenSecret)

api = tweepy.API(auth)

public_tweets = api.home_timeline()
for tweet in public_tweets:
    print(tweet.text)