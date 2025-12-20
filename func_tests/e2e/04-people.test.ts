import { test, expect } from '@playwright/test';
import { PeoplePage } from '../page-objects/PeoplePage';
import { APIClient } from '../helpers/api-client';
import { TestData } from '../helpers/test-data';

test.describe.skip('People Management', () => {
  let peoplePage: PeoplePage;
  let apiClient: APIClient;
  let testImages: string[] = [];

  test.beforeAll(async () => {
    apiClient = new APIClient();
    await apiClient.initialize();
    testImages = await TestData.createTestImages(5);
  });

  test.afterAll(async () => {
    // Clean up any people created during the tests
    const response = await apiClient.getPeople();
    const people = await response.json();
    for (const person of people) {
      await apiClient.deletePerson(person.id);
    }
    await apiClient.dispose();
  });

  test.beforeEach(async ({ page }) => {
    peoplePage = new PeoplePage(page);
    await peoplePage.goto('/people');
  });

  test('adds a new person with selected photos', async () => {
    const personName = TestData.getRandomPersonName();
    await peoplePage.addPerson(personName, testImages.slice(0, 3));

    const people = await peoplePage.getAllPeople();
    expect(people).toContain(personName);
  });

  test('requires name and photos before saving', async () => {
    await peoplePage.addPersonButton.click();

    // Save disabled initially
    expect(await peoplePage.savePersonButton.isDisabled()).toBeTruthy();

    // Enter name but no photos yet
    await peoplePage.personNameInput.fill('Validation Test');
    expect(await peoplePage.savePersonButton.isDisabled()).toBeTruthy();

    // Select a photo to enable save
    const gridItem = peoplePage.page.locator('.grid.grid-cols-6 > div').first();
    await gridItem.waitFor({ state: 'visible', timeout: 10000 });
    await gridItem.click();
    expect(await peoplePage.savePersonButton.isEnabled()).toBeTruthy();
  });

  test('filters people by name search', async () => {
    const alice = 'Alice Search';
    const bob = 'Bob Search';

    await peoplePage.addPerson(alice, [testImages[0]]);
    await peoplePage.addPerson(bob, [testImages[1]]);

    await peoplePage.searchPerson('Alice');
    const visibleCards = await peoplePage.page
      .locator('[data-testid="person-item"]:visible')
      .allTextContents();

    expect(visibleCards.some(text => text.includes(alice))).toBeTruthy();
    expect(visibleCards.some(text => text.includes(bob))).toBeFalsy();
  });

  test('disables find photos when face search is off', async () => {
    await apiClient.updateConfig({ face_search_enabled: false });
    await peoplePage.goto('/people');

    const name = 'Face Off Test';
    await peoplePage.addPerson(name, [testImages[0]]);

    const card = peoplePage.page.locator('[data-testid="person-item"]', { hasText: name }).first();
    const findButton = card.locator('button:has-text("Find Photos")');
    await findButton.waitFor({ state: 'visible', timeout: 5000 });
    expect(await findButton.isDisabled()).toBeTruthy();

    // Restore for other tests
    await apiClient.updateConfig({ face_search_enabled: true });
  });

  test('deletes a person after confirmation', async () => {
    const personName = 'Delete Flow Test';
    await peoplePage.addPerson(personName, [testImages[0]]);

    await peoplePage.deletePerson(personName);

    const people = await peoplePage.getAllPeople();
    expect(people).not.toContain(personName);
  });
});