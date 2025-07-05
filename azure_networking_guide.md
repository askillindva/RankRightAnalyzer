# Azure OpenAI Networking Configuration Guide

## Current Replit Environment Details
- **Current IP Address**: 34.9.104.227 (Dynamic - changes on restart)
- **Provider**: Google Cloud Platform (Replit's infrastructure)
- **Region**: Likely US-based but varies

## Security Options for Azure OpenAI Access

### Option 1: Allow All Networks (Least Secure)
**Best for**: Development and testing
```
Azure Portal → Your OpenAI Resource → Networking
- Select "All networks"
- Click Save
```

### Option 2: Specific IP Whitelisting (Temporary)
**Best for**: Short-term access with current IP
```
Azure Portal → Your OpenAI Resource → Networking
- Select "Selected networks"
- Add IP: 34.9.104.227
- Click Save
```
**Warning**: This IP will change when Replit restarts your environment.

### Option 3: Azure Service Tags (Recommended)
**Best for**: Secure access from Azure services
```
Azure Portal → Your OpenAI Resource → Networking
- Select "Selected networks"
- Under "Service Tags", add:
  - AzureCloud (all Azure services)
  - Or specific region like AzureCloud.EastUS
- Click Save
```

### Option 4: Virtual Network Integration (Most Secure)
**Best for**: Production environments with dedicated infrastructure

**Requirements**:
1. Deploy application to Azure Container Instances or App Service
2. Create Virtual Network (VNet)
3. Configure Private Endpoints

**Steps**:
```
1. Create Azure Container Instances in a VNet
2. Deploy RankRight application to the container
3. Configure Azure OpenAI with Private Endpoint
4. Restrict access to VNet only
```

## Replit Limitations

**What Replit Cannot Provide**:
- Static IP addresses
- Private endpoints
- Virtual network integration
- Dedicated network infrastructure

**Current Architecture**:
- Replit runs on shared Google Cloud infrastructure
- IP addresses are dynamic and shared
- No control over network routing

## Recommended Production Architecture

For production deployment with proper network security:

```
Internet → Azure Front Door → Azure App Service (VNet) → Azure OpenAI (Private Endpoint)
```

**Benefits**:
- Static IP ranges via Azure
- Private network communication
- Web Application Firewall protection
- SSL termination and caching

## Implementation Steps for Secure Production

1. **Deploy to Azure**:
   ```bash
   # Create resource group
   az group create --name rankright-rg --location eastus
   
   # Create App Service Plan
   az appservice plan create --name rankright-plan --resource-group rankright-rg --sku B1 --is-linux
   
   # Create Web App
   az webapp create --name rankright-app --resource-group rankright-rg --plan rankright-plan --runtime "PYTHON|3.11"
   ```

2. **Configure Virtual Network**:
   ```bash
   # Create VNet
   az network vnet create --name rankright-vnet --resource-group rankright-rg --subnet-name default
   
   # Integrate App Service with VNet
   az webapp vnet-integration add --name rankright-app --resource-group rankright-rg --vnet rankright-vnet --subnet default
   ```

3. **Configure Azure OpenAI**:
   - Set networking to "Selected networks"
   - Allow traffic from the VNet only
   - Optionally configure Private Endpoint

## Quick Fix for Current Development

For immediate development access, use **Option 2** (IP whitelisting):
1. Add IP `34.9.104.227` to Azure OpenAI allowed list
2. Remember to update when IP changes
3. Consider moving to Azure deployment for production