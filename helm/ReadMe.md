# Standalone or Normal Mode?

According to [docs.mau.fi](https://docs.mau.fi/maubot/usage/standalone.html)

> The normal mode in maubot is very dynamic: the config file doesn't really contain any runtime details other than a general web server, database, etc. Everything else is set up at runtime using the web management interface or the management API directly. This dynamicness is very useful for developing bots and works fine for deploying it on personal servers, but it's not optimal for larger production deployments.
The solution is standalone mode: a separate entrypoint that runs a single maubot plugin with a predefined Matrix account.
Additionally, standalone mode supports using appservice transactions to receive events instead of /sync, which is often useful for huge production instances with lots of traffic. 

---

> [!NOTE]  
> unlike Normal Mode, the Standalone Mode will not create an SQlite db for you (if no postgres is specified) . You'll have to create one yourself

# Normal Mode Steps

## After Deployment

After deploying the Bot Framework you can navigate to the web interface and login with a User you specified in your Values's `admin` block.

To use the maubot framework however you need to:

1. register a user that the bot should use on your specified homeserver
> [!NOTE]  
> you can skip the first step if you have a sharedSecret of your homeserver configured

2. connect to the container with 
```bash
    kubectl exec -it deployments/maubot -- sh
```
 3. run `mbc auth` with the user you want your bot to use. Note down the Access Token and device_id as you will need to enter these in the UI or in your config for future deployments.

    You may use the `--register` and `--update-client` flags to register a new user for your bot and make the pod store the access token.

## Plugins

You can find available "plugins", other bots that use the maubot framework at https://plugins.mau.bot

## add Plugins

see https://docs.mau.fi/maubot/usage/basic.html#uploading-plugins