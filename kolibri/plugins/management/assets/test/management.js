/* eslint-env mocha */
// The following two rules are disabled so that we can use anonymous functions with mocha
// This allows the test instance to be properly referenced with `this`
/* eslint prefer-arrow-callback: "off", func-names: "off" */
const Vue = require('vue');
const Vuex = require('vuex');
const assert = require('assert');
const _ = require('lodash');

const { store, mutations, constants } = require('../src/vuex/store.js');
const Management = require('../src/main.vue');
const fixture1 = require('./fixtures/fixture1.js');


describe('The management module', () => {
  it('defines a Management vue', () => {
    // A sanity check
    assert(Management !== undefined);
  });

  describe('has the following components:', function () {
    before(function () {
      const container = new Vue({
        template: '<div class="foo"><management v-ref:main></management></div>',
        components: { Management },
        store,
      }).$mount();
      this.vm = container.$refs.main;
    });

    after(function () {
      this.vm.$destroy();
    });

    it('a classroom selector', function (done) {
      Vue.nextTick(() => {
        const child = this.vm.$refs.classroomSelector;
        assert.notStrictEqual(child, undefined);
        done();
      });
    });

    it('a learner group selector', function (done) {
      Vue.nextTick(() => {
        const child = this.vm.$refs.learnerGroupSelector;
        assert.notStrictEqual(child, undefined);
        done();
      });
    });

    it('a learner roster', function (done) {
      Vue.nextTick(() => {
        const child = this.vm.$refs.learnerRoster;
        assert.notStrictEqual(child, undefined);
        done();
      });
    });
  });

  describe('changes the list of students in the roster when you select a classroom.', function () {
    beforeEach(function () {
      const testStore = new Vuex.Store({
        state: fixture1,
        mutations,
      });
      const container = new Vue({
        template: '<div><management v-ref:main></management></div>',
        components: { Management },
        store: testStore,
      }).$mount();
      this.vm = container.$refs.main;
      this.store = testStore;
    });

    afterEach(function () {
      this.vm.$destroy();
    });

    it('The roster shows only John Duck when you select "Classroom C".', function (done) {
      // Look at the fixture file for the magic numbers here.
      this.store.dispatch('SET_SELECTED_CLASSROOM_ID', 3);
      Vue.nextTick(() => {
        assert(_.isEqual(this.vm.$refs.learnerRoster.learners, [{
          id: 2,
          first_name: 'John',
          last_name: 'Duck',
          username: 'jduck',
        }]));
        done();
      });
    });

    it('The roster shows all learners when you select "All classrooms".', function (done) {
      this.store.dispatch('SET_SELECTED_CLASSROOM_ID', constants.ALL_CLASSROOMS_ID);
      Vue.nextTick(() => {
        assert(_.isEqual(this.vm.$refs.learnerRoster.learners, fixture1.learners));
        done();
      });
    });
  });
});
