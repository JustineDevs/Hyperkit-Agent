// Deployment script for TestToken
const TestToken = artifacts.require("TestToken");

module.exports = async function (deployer, network, accounts) {
    const owner = accounts[0];
    
    console.log("Deploying TestToken...");
    
    await deployer.deploy(TestToken, {
        from: owner,
        gas: 3000000
    });
    
    const TestToken = await TestToken.deployed();
    console.log("TestToken deployed at:", TestToken.address);
    
    // Add any post-deployment setup here
};
