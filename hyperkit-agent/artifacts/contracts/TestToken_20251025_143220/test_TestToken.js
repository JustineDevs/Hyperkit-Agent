// Test file for TestToken
const TestToken = artifacts.require("TestToken");

contract("TestTokenTest", (accounts) => {
    let TestToken;
    const owner = accounts[0];
    const user1 = accounts[1];
    const user2 = accounts[2];

    beforeEach(async () => {
        TestToken = await TestToken.new({ from: owner });
    });

    it("should deploy successfully", async () => {
        assert.ok(TestToken.address);
    });

    it("should have correct owner", async () => {
        const contractOwner = await TestToken.owner();
        assert.equal(contractOwner, owner);
    });

    // Add more tests as needed
});
